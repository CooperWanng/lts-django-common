from rest_framework.viewsets import ModelViewSet
from .filters import LuSearchFilterBackend, LuOrderFilterBackend, LuDistinctFilterBackend, LuResponseFieldFilterBackend
from django_filters.rest_framework.backends import DjangoFilterBackend
from .paginations import LuPagination


class LuModelViewSet(ModelViewSet):
    filter_backends = (
        DjangoFilterBackend,
        LuSearchFilterBackend,
        LuOrderFilterBackend,
        LuDistinctFilterBackend,
        LuResponseFieldFilterBackend
    )
    pagination_class = LuPagination
