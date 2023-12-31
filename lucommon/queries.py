from django.db import models
from .utils import get_cur_user
from copy import deepcopy
from .settings import lu_settings
from .exceptions import LuLockError
import json

VERSION = lu_settings.OPTIMISTIC_LOCK_FIELD
IS_IDEMPOTENT_CHECK = lu_settings.OPTIMISTIC_LOCK_CHECK
UpdaterField = lu_settings.UPDATER_FIELD
CreatorField = lu_settings.CREATOR_FIELD


class LuHistory(models.Model):
    """
    CREATE TABLE `lu_history` (
      `id` bigint(20) NOT NULL AUTO_INCREMENT,
      `type_id` bigint(20) NOT NULL,
      `type` varchar(255) NOT NULL,
      `diff` text NOT NULL,
      `operation` varchar(255) NOT NULL,
      `created_at` datetime(6) NOT NULL,
      `created_by` varchar(255) DEFAULT NULL,
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=1;
    """
    type_id = models.BigIntegerField()
    type = models.CharField(max_length=255)
    diff = models.TextField()
    operation = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255)

    class Meta:
        db_table = lu_settings.HISTORY_TABLE


def _filter_private_attr(obj: dict):
    return {k: v for k, v in obj.items() if not str(k).startswith('_')}


def _calculate_diff(new: dict, old: dict):
    new = _filter_private_attr(new)
    old = _filter_private_attr(old)
    diff = {}

    if not old:
        # insert
        for attr in new:
            diff[attr] = {'new': str(new[attr]), 'old': None}
    elif not new:
        # delete
        for attr in old:
            diff[attr] = {'new': None, 'old': str(old[attr])}
    else:
        # update
        for attr in new:
            new_value, old_value = new[attr], old[attr]
            if new_value != old_value:
                diff[attr] = {'new': str(new_value), 'old': str(old_value)}
    return diff


def _save_history(type_id, type, diff, operation, created_by):
    # todo async
    if lu_settings.SAVE_HISTORY:
        if diff:
            data = dict(
                type_id=type_id,
                type=type,
                diff=json.dumps(diff),
                operation=operation,
                created_by=created_by
            )
            LuHistory.objects.using('default').create(**data)


def _idempotent_check(model: models.Model, data: dict):
    """
    幂等校验
    :param model: 更新前的model
    :param data:
    :return:
    """
    if hasattr(model, VERSION) and VERSION in data:
        current_version = getattr(model, VERSION)
        request_version = data[VERSION]
        if current_version != request_version:
            raise LuLockError('数据已经被修改，请尝试刷新页面后重试')
        return True
    return


class LuQuerySet(models.QuerySet):
    """
    LuQuerySet在QuerySet的基础上做了什么
    I、指定字段默认赋值，如果model中定义了这些字段，且未赋值
        1、每次更新对更新人默认赋值为当前用户
        2、每次新建对创建人默认赋值为当前用户
    II、对新增、修改操作进行记录留痕
        1、_insert()对新增记录做留痕处理
        2、bulk_create()不会记录创建历史，因为无法获取批量插入数据的id，也不会造成额外开销
        3、_update()对修改操作做留痕处理，相比于父类方法，会额外产生一次数据库查询开销
        4、update()对修改操作做留痕处理，相比于父类方法，会产生两次数据库查询开销
        5、bulk_update() todo
    III、更新操作进行幂等校验
        1、_update()通过乐观锁实现幂等
        2、update()不做乐观锁控制,queryset中不同model可能拥有不同的version，但是在执行update方法时，传入的kwargs只能指定
        一个version，这样乐观锁校验必然失败
        3、bulk_update()->update()，同上
    """

    # todo 抽取自动赋值创建人、更新人
    # todo 抽取乐观锁校验

    def _insert(self, objs, fields, returning_fields=None, raw=False, using=None, ignore_conflicts=False):
        cur_user = get_cur_user()
        model = objs[0]
        if hasattr(model, CreatorField):
            if not getattr(model, CreatorField):
                setattr(model, CreatorField, cur_user)
        insert_result = super()._insert(objs, fields, returning_fields, raw, using, ignore_conflicts)
        if insert_result:
            # 批量插入不返回id
            model_copy = deepcopy(model)  # 不对元数据做修改
            model_copy.pk = insert_result[0][0]
            mode_dict = model_copy.__dict__
            diff = _calculate_diff(new=mode_dict, old={})
            _save_history(
                type_id=model_copy.pk, type=model_copy.__class__._meta.db_table,
                diff=diff, operation='create', created_by=cur_user
            )
        return insert_result

    def _update(self, values):
        cur_user = get_cur_user()
        model = self[0]
        pk = model.id
        old_dict = deepcopy(model.__dict__)
        new_dict = {}
        values_index_dict = {}
        for i, v in enumerate(values):
            # 获取values中每个字段的位置
            # 获取待更新的字段值
            values_index_dict[v[0].name] = i
            new_dict[v[0].name] = v[2]

        if UpdaterField in old_dict:
            if new_dict.get(UpdaterField) is None:
                _index = values_index_dict[UpdaterField]
                tmp = list(values[_index])
                tmp[2] = cur_user
                values[_index] = tuple(tmp)
                new_dict[UpdaterField] = cur_user

        if IS_IDEMPOTENT_CHECK:
            if _idempotent_check(model, new_dict) is True:
                _index = values_index_dict[VERSION]
                tmp = list(values[_index])
                tmp[2] += 1
                values[_index] = tuple(tmp)

        update_result = super()._update(values)
        if update_result > 0:
            diff = _calculate_diff(new=new_dict, old=old_dict)
            _save_history(
                type_id=pk, type=model.__class__._meta.db_table,
                diff=diff, operation='update', created_by=cur_user
            )
        return update_result

    def update(self, **kwargs):
        old_models = [model for model in self.order_by('pk')]
        update_result = super().update(**kwargs)
        new_models = [model for model in self.order_by('pk')]
        wait_to_diffs = zip(new_models, old_models)
        for new, old in wait_to_diffs:
            pk = new.pk
            diff = _calculate_diff(new.__dict__, old.__dict__)
            _save_history(
                type_id=pk, type=new.__class__._meta.db_table,
                diff=diff, operation='update', created_by=get_cur_user()
            )
        return update_result
