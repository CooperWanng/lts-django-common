from django.conf import settings as django_settings
from collections import OrderedDict


def insert_middleware():
    """
    django启动后，依次插入以下中间件
    1、django.middleware.common.CommonMiddleware前放置corsheaders.middleware.CorsMiddleware
    2、用户自定义middleware前放置crum.CurrentRequestUserMiddleware
    :return:
    """

    middleware_list = django_settings.MIDDLEWARE
    order_list = []

    # todo 判断用户是否已经添加相关中间件或者app
    for i, m in enumerate(middleware_list):
        if m == "django.middleware.common.CommonMiddleware":
            order_list.append((i, "corsheaders.middleware.CorsMiddleware"))
        if not m.startswith("django") and middleware_list[i - 1].startswith("django"):
            order_list.append((i, "crum.CurrentRequestUserMiddleware"))
    order_list.sort(key=lambda x: x[0], reverse=True)

    for (i, m) in order_list:
        middleware_list.insert(i, m)


"""添加配置"""
# todo 判断用户是否已经添加相关中间件或者app
django_settings.DATABASE_ROUTERS.append('lucommon.database_router.DataBaseRouter')
django_settings.INSTALLED_APPS.append("rest_framework")
django_settings.INSTALLED_APPS.append("drf_yasg")

insert_middleware()

"""添加配置"""


class LuConfig:
    def __init__(self, value, type, desc=''):
        self.default_value = value
        self.type = type
        self.desc = desc


class LuSettings:

    def __new__(cls, *args, **kwargs):
        instance = 'instance'
        if not hasattr(cls, instance):
            setattr(cls, instance, super().__new__(cls, *args, **kwargs))
        return getattr(cls, instance)

    def __init__(self):
        user_setting = dict()
        if hasattr(django_settings, "LU_COMMON"):
            user_setting = getattr(django_settings, "LU_COMMON")

        for attr, config in DEFAULT_ATTR.items():
            if attr in user_setting:
                if not isinstance(user_setting[attr], config.type):
                    raise TypeError("attr {} must be {} object".format(attr, config.type))
                setattr(self, attr, user_setting[attr])
            else:
                setattr(self, attr, config.default_value)

    def to_dict(self):
        tmp = OrderedDict()
        for attr in dir(self):
            tmp[attr] = getattr(self, attr)

        return tmp


# 有序字典
DEFAULT_ATTR = {
    'SEARCH_FIELD': LuConfig('lu_search_field', str, '查询字段'),
    'SEARCH_VALUE': LuConfig('lu_search_value', str, '查询值'),
    'SEARCH_TYPE': LuConfig('lu_search_type', str, '查询类型'),
    'SEARCH_DELIMITER': LuConfig(',', str, '多个查询条件下字段、值、类型的分隔符'),
    'SEARCH_VALUE_DELIMITER': LuConfig('|', str, '查询值包含多个值的分隔符'),  # todo 这两个不能一样，运行时校验

    'FILTER_NULL_VALUE': LuConfig('__NULL_VALUE__', str, 'filter中所定义的空值'),

    'RESPONSE_FIELD': LuConfig('lu_response_field', str, '查询记录所显示字段'),
    'RESPONSE_FIELD_DELIMITER': LuConfig(',', str, '查询记录所显示字段分隔符'),

    'PAGINATION_LIMIT_FIELD': LuConfig('lu_limit', str, '分页-每页记录条数'),
    'PAGINATION_OFFSET_FIELD': LuConfig('lu_offset', str, '分页-偏移量'),
    "PAGINATION_UN_LIMIT_VALUE": LuConfig("-1", str, "分页-展示所有数据"),
    'PAGINATION_DEFAULT_LIMIT': LuConfig(10, int, '分页-默认分页'),
    'PAGINATION_MAX_LIMIT': LuConfig(1000, int, '分页-最大分页'),

    "ORDER_FILED": LuConfig("lu_order_field", str, "排序字段"),
    "ORDER_FILED_DELIMITER": LuConfig(",", str, "排序字段分割符"),

    "DISTINCT_FIELD": LuConfig("lu_response_distinct", str, "是否去重字段"),
    "IS_DISTINCT_VALUE": LuConfig("1", str, "数据需要去重是所传的值"),

    'OPTIMISTIC_LOCK_CHECK': LuConfig(True, bool, '是否开启更新乐观锁检查'),
    'OPTIMISTIC_LOCK_FIELD': LuConfig('version', str, '乐观锁字段'),
    'CREATOR_FIELD': LuConfig('created_by', str, '字段-创建人'),
    'UPDATER_FIELD': LuConfig('updated_by', str, '字段-更信任'),

    'SAVE_HISTORY': LuConfig(True, bool, '是否开启更新历史记录'),
    'HISTORY_TABLE': LuConfig('lu_history', str, '历史记录表名'),

    "PRIMARY_KEY": LuConfig("id", str, "数据表主键"),

    "LOG_DIR": LuConfig("", str, "日志目录"),
    "LOG_FILE": LuConfig("lu_common.log", str, "日志名称"),
    "LOG_LEVEL": LuConfig("INFO", str, "日志等级"),
    "LOG_WHEN": LuConfig("midnight", str, "日志分隔协议")
}

lu_settings = LuSettings()
