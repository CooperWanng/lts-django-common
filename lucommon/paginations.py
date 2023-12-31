from rest_framework import pagination
from rest_framework.response import Response
from collections import OrderedDict
from .settings import lu_settings


class LuPagination(pagination.LimitOffsetPagination):
    limit_query_param = lu_settings.PAGINATION_LIMIT_FIELD
    offset_query_param = lu_settings.PAGINATION_OFFSET_FIELD
    default_limit = lu_settings.PAGINATION_DEFAULT_LIMIT
    max_limit = lu_settings.PAGINATION_MAX_LIMIT
    un_limit_value = lu_settings.PAGINATION_UN_LIMIT_VALUE

    def get_paginated_response(self, data):
        return Response({
            'data': data,
            'pagination': OrderedDict({
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'count': self.count
            })
        })

    def paginate_queryset(self, queryset, request, view=None):
        self.count = self.get_count(queryset)
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None
        if self.limit == self.un_limit_value:
            self.limit = self.count

        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return list(queryset[self.offset:self.offset + self.limit])

    def get_limit(self, request):
        if self.limit_query_param:
            try:
                limit_value = request.query_params[self.limit_query_param]
                if limit_value == self.un_limit_value:
                    return self.un_limit_value
                return pagination._positive_int(
                    limit_value,
                    strict=True,
                    cutoff=self.max_limit
                )
            except (KeyError, ValueError):
                pass

        return self.default_limit
