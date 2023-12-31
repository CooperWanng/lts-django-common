from django.db import models
from .managers import LuManager


class LuModel(models.Model):
    objects = LuManager()

    class Meta:
        abstract = True

        default_manager_name = 'objects'
        base_manager_name = 'objects'

    @classmethod
    def db_for_read(cls, **hints):
        """
        这里定义查询操作时，所指定的数据库

        """
        pass

    @classmethod
    def db_for_write(cls, **hints):
        """
        这里定义写入操作时，所指定的数据库

        """
        pass
