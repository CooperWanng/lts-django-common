import django_filters
from django_filters.constants import EMPTY_VALUES as _EMPTY_VALUES
from .settings import lu_settings

__FILTER__ = "__FILTER__"
__EXCLUDE__ = "__EXCLUDE__"


def _patch_filter(self, qs, value):
    if value in _EMPTY_VALUES:
        return qs
    if value == lu_settings.LU_FILTER_NULL_VALUE:
        value = None
    if self.distinct:
        qs = qs.distinct()
    lookup = '%s__%s' % (self.field_name, self.lookup_expr)
    try:
        qs = self.get_method(qs)(**{lookup: value})
    except:
        return qs.none()
    return qs


def _patch_filter_queryset(self, queryset):
    for name, value in self.form.data.items():
        filter = self.filters.get(name)
        if filter:
            queryset = filter.filter(queryset, value)
    return queryset


django_filters.filterset.BaseFilterSet.filter_queryset = _patch_filter_queryset
django_filters.filters.Filter.filter = _patch_filter
django_filters.rest_framework.backends.DjangoFilterBackend.raise_exception = False


class LuFilterSet(django_filters.rest_framework.FilterSet):
    pass


class _LookUp:
    def __init__(self, lookup, filter_type, desc):
        """
        :param lookup: django orm 中的定义的查找字段 文档:https://docs.djangoproject.com/zh-hans/3.2/ref/models/querysets/#field-lookups
        :param filter_type: 查找类型，正向查找、反向查找
        :param desc: 描述
        """
        self.lookup = lookup
        self.filter_type = filter_type
        self.desc = desc


class LuSearchFilterBackend:
    SearchField = lu_settings.SEARCH_FIELD
    SearchValue = lu_settings.SEARCH_VALUE
    SearchType = lu_settings.SEARCH_TYPE
    SearchDelimiter = lu_settings.SEARCH_DELIMITER
    SearchValueDelimiter = lu_settings.SEARCH_VALUE_DELIMITER
    DefaultSearchType = _LookUp("exact", __FILTER__, "等于")
    LookUpMap = {
        '0': _LookUp("contains", __FILTER__, "区分大小写的包含匹配"),
        '1': _LookUp("startswith", __FILTER__, "区分大小写的开头匹配"),
        '2': _LookUp("exact", __FILTER__, "完全匹配"),
        '3': _LookUp("regex", __FILTER__, "区分大小写的正则表达式匹配"),
        '4': _LookUp("contains", __EXCLUDE__, "区分大小写的包含匹配"),
        '5': _LookUp("startswith", __EXCLUDE__, "区分大小写的开头匹配"),
        '6': _LookUp("exact", __EXCLUDE__, "完全匹配"),
        '8': _LookUp("in", __FILTER__, "在"),
        '9': _LookUp("in", __EXCLUDE__, "不在"),
    }

    def _get_search_info(self, request, search_category):
        category = request.query_params.get(search_category)
        category_list = category.split(self.SearchDelimiter) if category else []
        return tuple(category_list)

    def _trans_search_type_to_lookup(self, search_type):
        result = []
        for t in search_type:
            lookup = self.LookUpMap.get(str(t))
            result.append(lookup if lookup else self.DefaultSearchType)
        return result

    def _generate_search_set(self, request):
        # return generator as (search_field,search_value,search_lookup)
        return zip(
            self._get_search_info(request, self.SearchField),
            self._get_search_info(request, self.SearchValue),
            self._trans_search_type_to_lookup(self._get_search_info(request, self.SearchType))
        )

    def _get_lookups_dict(self, search_set):
        filters_lookup = {}
        excludes_lookup = {}
        for (field, value, lookup) in search_set:
            value = None if value == lu_settings.FILTER_NULL_VALUE else value
            if lookup.lookup in ['in']:
                value = value.split(self.SearchValueDelimiter) if value else []
            lookup_name = '{}__{}'.format(field, lookup.lookup)
            if lookup.filter_type == __FILTER__:
                filters_lookup[lookup_name] = value
            if lookup.filter_type == __EXCLUDE__:
                excludes_lookup[lookup_name] = value

        return filters_lookup, excludes_lookup

    def _render_queryset(self, queryset, filters_lookups, excludes_lookups):
        queryset = queryset.filter(**filters_lookups) if filters_lookups else queryset

        """
        这里exclude两种实现方式
        1、exclude(**excludes_lookups)
        对应SQL：where not (cond1 and cond2 and ...)
        逻辑：每个条件是 或 连接
        
        2、遍历excludes_lookups，每次插入一条excludes_lookup，生成新的queryset
        对应SQL：where not cond1 and not cond2 and ...
        逻辑：每个条件是 与 连接
        """
        # queryset = queryset.exclude(**excludes_lookups) if excludes_lookups else queryset
        for k, v in excludes_lookups.items():
            queryset = queryset.exclude(**{k: v})

        return queryset

    def filter_queryset(self, request, queryset, view):
        search_set = self._generate_search_set(request)
        filters_lookups, excludes_lookups = self._get_lookups_dict(search_set)

        queryset = self._render_queryset(queryset, filters_lookups, excludes_lookups)

        return queryset


class LuOrderFilterBackend:
    OrderField = lu_settings.ORDER_FILED
    OrderFieldDelimiter = lu_settings.ORDER_FILED_DELIMITER

    def get_order_fields(self, request):
        order_fields_str = request.query_params.get(self.OrderField)
        fields = order_fields_str.split(self.OrderFieldDelimiter) if order_fields_str else []
        return fields

    def filter_queryset(self, request, queryset, view):
        order_fields = self.get_order_fields(request)
        queryset = queryset.order_by(*order_fields)
        return queryset


class LuDistinctFilterBackend:
    DistinctField = lu_settings.DISTINCT_FIELD
    DistinctValue = lu_settings.IS_DISTINCT_VALUE

    def is_distinct(self, request):
        distinct_value = request.query_params.get(self.DistinctField)
        if distinct_value == self.DistinctValue:
            return True
        return False

    def filter_queryset(self, request, queryset, view):
        if self.is_distinct(request):
            return queryset.distinct()
        return queryset


class LuResponseFieldFilterBackend:
    SearchField = lu_settings.RESPONSE_FIELD
    SearchValueDelimiter = lu_settings.RESPONSE_FIELD_DELIMITER

    def _get_fields(self, request):
        values = request.query_params.get(self.SearchField)
        values_list = values.split(self.SearchValueDelimiter) if values else []
        return tuple(values_list)

    def _get_model_fields(self, view):
        model = getattr(view, 'model', view.queryset.model)
        valid_fields = [field.name for field in model._meta.fields]
        return tuple(valid_fields)

    def filter_queryset(self, request, queryset, view):
        response_fields = self._get_fields(request)
        model_fields = self._get_model_fields(view)
        valid_response_fields = tuple(set(model_fields) & set(response_fields))

        if valid_response_fields:
            return queryset.values(*valid_response_fields)
        # todo 仅查询
        # todo 如果涉及到 methodSerializerField 字段的展示，返回原生queryset
        return queryset
