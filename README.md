背景

```
利用Django进行后端的开发已经相当便利和简单，MVT模式让开发者更加关注自己的业务逻辑处理，代码结构规范，便于阅读和维护。
不少公司，开发比较大的项目，常采用前后端分离：后端提供数据，如何渲染数据全权交由前端负责。由传统的轻Client重Server到重Client轻Server的转化，将数据的分析提供和数据的显示分离。如同一套接口，网站（web），移动（IOS, Android）调用做出不同的UI，对于前后端开发人员，职责更清晰。

在调研常用后端框架（flask-restful, djangorestframewok）的基础上，结合项目本身的需求和一些常用规范，框架组会在restframework的基础上进一步封装，打造一个基于restful的通用的后端处理框架 lucommon

```

介绍

```
lucommon基于rest framework进行二次封装，而且充分利用python里一些优质的模块，如django-filters, django-rest-swagger等。关于这些框架或者模块的介绍，请自行查阅相关文档，以便深入学习。

本文的一个最基本目的，是对利用django开发有一些基础知识的人，能够快速将lucommon集成到自己的项目中去。

另外，以lucommon作为切入点，把一些常用的优质模块拿过来，然后在实际项目中，如何把他们集中在一起编写应用。因此，如果你不想花太多精力去阅读各个优质模块的文档，想简单通过本文的介绍，快速利用这些技术开发你的第一个应用，也是我们框架的一个目的
```

基本功能

* 集成查询过滤器
* 集成异常处理器
* 集成查询分页器
* 统一响应格式
* 内置乐观锁
* 内置更新记录
* 自动赋值操作用户
* 自动生成、添加代码
* 多数据库配置
* 日志配置
* 生成接口返回规范结果
* 接口文档自动生成

安装

# 用户如何进行配置

* 配置项代码示例

```python
# settings.py

LU_COMMON = {
    "attr": "value",
    ...
}
```

* 具体配置项可参考功能模块

# 模块

### 日志

```
通过python自带的logging模块，封装StreamHandler、TimedRotatingFileHandler，实现可分割文件的日志handler
```

* 用户配置项

| 参数值 | 类型 | 含义 | 默认值 |
| :-----| :----: | :----: | :----: |
| LOG_DIR | string | 日志存放目录 | 根目录 |
| LOG_FILE | string | 日志文件名称 | lu_common.log |
| LOG_LEVEL | string | 日志等级 | INFO |
| LOG_WHEN | string | 日志分隔协议 | midnight |

* 使用示例

```python
from lucommon.logger import lu_logger

lu_logger.info("xxx")
lu_logger.error("xxx")

```

```
2022-08-17 15:21:14,869.869 INFO Thread-1 views.py:33 - xxx
2022-08-17 15:21:14,870.870 ERROR Thread-1 views.py:35 - xxx
```

### 多数据库

```
用户可通过自定义model中的钩子函数来确定读写数据库，若无定义，默认使用 default 数据库
```

* 用户配置项 无

* 使用示例

```python
from django.db import models


class UserModel(models.Model):
    ...

    class Meta:
        ...

    @classmethod
    def db_for_read(cls, **hints):
        # 这里配置读取操作时所使用的数据库
        # do something
        return "database_alias1"

    @classmethod
    def db_for_write(cls, **hints):
        # 这里配置写入操作时所使用的数据库
        # do something
        return "database_alias2"
```

### 序列化器

```
基于restframework的ModelSerializes
拓展了对于MethodSerializeField字段的批量查询功能
```

```python
from lucommon.serializers import LuModelSerializer
from rest_framework import serializers


# 关联字段批量查询方法
class UserModelSerializer(LuModelSerializer):
    abc = serializers.SerializerMethodField()

    def _get_multi_abc(self, pk_list):
        # 这里通过 self.model_pks 批量执行关联查询，返回所有查询结果

        return {"pk": "value"}

    def get_abc(self, obj):
        # 这里通过使用 lazy_cache 调用 批量查询方法
        self.lazy_cache(self._get_multi_abc).get(obj.id)

```

### 查询

```
lucommon提供了多种查询方式
前端用户可通过

实现获取所有数据的功能
```
##### 搜索查询



##### 分页查询

* 用户配置项

| 参数值 | 类型 | 含义 | 默认值 |
| :-----| :----: | :----: | :----: |
| PAGINATION_LIMIT_FIELD | string | url查询条件中页码字段 | lu_limit |
| PAGINATION_OFFSET_FIELD | string | url查询条件中偏移量字段 | lu_offset |
| PAGINATION_UN_LIMIT_VALUE | string | 当无需分页展示所有数据时，传给PAGINATION_LIMIT_FIELD的值 | -1 |
| PAGINATION_DEFAULT_LIMIT | int | 默认每页记录条数 | 10 |
| PAGINATION_MAX_LIMIT | int | 默认最大记录条数 | 1000 |

* 使用示例

```python
from lucommon.logger import lu_logger

lu_logger.debug("xxx")
lu_logger.error("xxx")
```


##### 排序查询

##### 去重查询
