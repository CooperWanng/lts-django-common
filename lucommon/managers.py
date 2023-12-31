from django.db import models
from .queries import LuQuerySet


class LuManager(models.Manager):

    def get_queryset(self):
        return LuQuerySet(model=self.model, using=self._db, hints=self._hints)
