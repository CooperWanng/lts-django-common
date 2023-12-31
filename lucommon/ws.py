import traceback

import django
import json
import asyncio
import uuid
import warnings
from django.core.handlers.asgi import ASGIHandler
from django.urls import resolve, Resolver404
from collections import OrderedDict
from django.conf import settings
from django.utils.module_loading import import_string
from django.http import Http404
from websockets.connection import State
from uvicorn.protocols.websockets.websockets_impl import WebSocketProtocol

'''
请求进来 WebSocketProtocol
process_request WebSocketProtocol
解析路由 WebSocketProtocol
process_view WebsocketConnection
执行view LuASGIHandler
'''


class ViewNotAsynchronous(Exception):
    pass


class LuWebSocketProtocol(WebSocketProtocol):
    async def process_request(self, path, headers):
        return (404,[],b'not found')

    async def run_asgi(self):
        try:
            result = await self.app(self.scope, self.asgi_receive, self.asgi_send)
        except Resolver404:
            pass  # todo
        except ViewNotAsynchronous as e:
            raise e
        except BaseException as e:
            self.closed_event.set()
            if not self.handshake_started_event.is_set():
                self.send_500_response()
            else:
                await self.handshake_completed_event.wait()
            self.transport.close()
        else:
            self.closed_event.set()
            if not self.handshake_started_event.is_set():
                msg = "ASGI callable returned without sending handshake."
                self.logger.error(msg)
                self.send_500_response()
                self.transport.close()
            elif result is not None:
                msg = "ASGI callable should return None, but returned '%s'."
                self.logger.error(msg, result)
                await self.handshake_completed_event.wait()

    def load_ws_middleware(self):
        pass


class WebsocketConnection:
    def __init__(self, ws_instance, ws_middleware=None):
        self._key = uuid.uuid4()
        self._instance: WebSocketProtocol = ws_instance
        self._middleware = ws_middleware if ws_middleware else []

        self._extra_headers = {}
        self.url = self._instance.scope.get('path') or self._instance.scope.get('raw_path')
        self.request_headers = {k.decode(): v.decode() for (k, v) in self._instance.scope.get('headers', [])}
        self.response_headers = {}
        self.params = {}
        self.client = self._instance.scope.get('client', tuple())
        for param in self._instance.scope.get('query_string').decode().split('&'):
            key, _, value = param.partition('=')
            self.params[key] = value

    @property
    def state(self):
        return self._instance.state

    def set_headers(self, headers: dict):
        if self.state == State.CONNECTING:
            self._extra_headers.update(headers)
        else:
            warnings.warn('websocket连接已建立或者关闭，无法添加响应头')

    def _adapt_view(self):
        res_result = resolve(self.url)
        view, args, kwargs = res_result
        if not asyncio.iscoroutinefunction(view):
            raise ViewNotAsynchronous('websocket view must be async')
        return view, args, kwargs

    async def _process_view(self):
        pass

    async def _confirm(self):
        await self._instance.asgi_receive()
        self._instance.extra_headers.extend([(str(k), str(v)) for k, v in self._extra_headers.items()])
        await asyncio.wait([self._instance.asgi_send({'type': 'websocket.accept'})])
        self.response_headers = {k: v for k, v in self._instance.response_headers.items()}

    async def close(self):
        await asyncio.wait([self._instance.asgi_send({'type': 'websocket.close'})])

    async def send(self, message):
        if self.state == State.OPEN:
            try:
                message = json.dumps(message)
            except:
                pass
            await self._instance.asgi_send({'type': 'websocket.send', 'text': message})

    async def receive(self):
        # todo json,add type to this method
        msg = await self._instance.asgi_receive()
        msg = msg.get('text')
        try:
            msg = json.loads(msg)
        except:
            pass
        return msg

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # todo 缓存、中间件连接等回收处理
        if self.state == State.OPEN:
            await self.close()
        print('websocket {} close'.format(self._key))

    def __bool__(self):
        return self.state == State.OPEN


class LuASGIHandler(ASGIHandler):
    websocket_class = WebsocketConnection

    def __init__(self):
        super().__init__()

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            async with self.websocket_class(receive.__self__) as ws_conn:
                res = ws_conn._adapt_view()
                ws_view, args, kwargs = res
                await ws_conn._confirm()  # websocket握手完成
                await ws_view(ws_conn, *args, **kwargs)

        else:
            await super().__call__(scope, receive, send)


def get_asgi_with_ws_application():
    django.setup(set_prefix=False)
    return LuASGIHandler()


from uvicorn.protocols.websockets import auto

# LuWebSocketProtocol.load_ws_middleware()
auto.AutoWebSocketsProtocol = LuWebSocketProtocol
