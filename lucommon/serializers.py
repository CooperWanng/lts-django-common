from rest_framework import serializers
from collections import OrderedDict
from .utils import __NoneValue__
from .settings import lu_settings
from django.db.models import QuerySet, Model


class LuModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_fields(kwargs['context']['request'])
        self.model_pks = self._get_model_pks()
        self._lazy_cache_result = {}

    def _filter_fields(self, request):
        fields = request.query_params.get(lu_settings.RESPONSE_FIELD)
        fields_list = fields.split(',') if fields else []
        if not fields_list:
            return

        serializer_fields = self.fields.fields
        valid_fields = set(serializer_fields) & set(fields_list)
        new_fields = OrderedDict()
        for f in valid_fields:
            new_fields[f] = serializer_fields[f]
        self.fields.fields = new_fields

    def get_attr(self, obj, attr):
        if isinstance(obj, Model):
            return getattr(obj, attr, None)
        if isinstance(obj, dict):
            return obj.get(attr, None)
        return

    def lazy_cache(self, func, *args, **kwargs):
        func_name = func.__name__
        value = self._lazy_cache_result.get(func_name, __NoneValue__)
        if value is __NoneValue__:
            new_value = func(*args, **kwargs)
            self._lazy_cache_result[func_name] = new_value
            return new_value

        return value

    def _get_pk(self, value):
        if isinstance(value, dict):
            pk = value.get(lu_settings.PRIMARY_KEY)
        else:
            pk = getattr(value, lu_settings.PRIMARY_KEY, None)

        return pk

    def _get_model_pks(self):
        result = []
        if isinstance(self.instance, (list, QuerySet)):
            result = [self._get_pk(instance) for instance in self.instance]
        if isinstance(self.instance, (dict, Model)):
            result = [self._get_pk(self.instance)]

        return tuple(result)
