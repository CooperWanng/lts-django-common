from crum import get_current_request as __get_current_request

__NoneValue__ = "__LU_COMMON_NONE_VALUE__"


def get_cur_user():
    # todo 这里配置化
    request = __get_current_request()
    user = getattr(request, "lts_user", None)
    if user:
        return str(user)
    return "anonymous"


def get_cur_request():
    return __get_current_request()
