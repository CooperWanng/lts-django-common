# coding=UTF-8


import logging
from logging import handlers
import uuid
import sys
import os
from .settings import lu_settings


class ColorFormatter(logging.Formatter):
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
    COLORS = {
        'WARNING': YELLOW,
        'INFO': WHITE,
        'DEBUG': BLUE,
        'CRITICAL': RED,
        'ERROR': RED
    }
    RESET_SEQ = '\033[0m'
    COLOR_SEQ = '\033[1;{}m'
    BOLD_SEQ = '\033[1m'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record):
        levelname = record.levelname
        color = self.COLOR_SEQ.format(30 + self.COLORS[levelname])
        message = logging.Formatter.format(self, record)
        message = message.replace('%RESET', self.RESET_SEQ) \
            .replace('%BOLD', self.BOLD_SEQ) \
            .replace('$COLOR', color)
        for k, v in self.COLORS.items():
            message = message.replace('$' + k, self.COLOR_SEQ.format(v + 30)) \
                .replace('$BG' + k, self.COLOR_SEQ.format(v + 40)) \
                .replace('$BG-' + k, self.COLOR_SEQ.format(v + 40))
        return message + self.RESET_SEQ


class Logger:
    LOGGER_STRUCTURE = {
        'time': '%(asctime)s.%(msecs)d',
        'message': '%(message)s',
        'level_name': '%(levelname)s',
        'line_no': '%(lineno)d',
        'function_name': '%(funcName)s',
        'thread_name': '%(threadName)s',
        'thread_id': '%(thread)d',
        'process_id': '%(process)d',
        'file_name': '%(filename)s',
        'color_position': '$COLOR'
    }

    def __init__(self, level, console=True, dir=None, file=None):
        '''
        :param level: 日志等级
        :param console: 是否打印日志
        :param file: 日志文件名称
        '''
        self._console_format = '{time} {color_position}{level_name} {thread_name} {file_name}:{line_no} - {message}'.format(
            **self.LOGGER_STRUCTURE)  # 打印格式

        self._file_format = '{time} {level_name} {thread_name} {file_name}:{line_no} - {message}'.format(
            **self.LOGGER_STRUCTURE)  # 文件格式

        self.level = level
        self._logger = logging.getLogger(str(uuid.uuid4()))
        self._logger.setLevel(self.level)
        if dir:
            if not os.path.isdir(dir):
                os.mkdir(dir)
        if console:
            self._add_console_log()
        if file:
            self._add_file_log(os.path.join(dir, file))

    def _add_console_log(self):
        stream_formatter = ColorFormatter(self._console_format)
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(stream_formatter)
        stream_handler.setLevel(self.level)
        self._logger.addHandler(stream_handler)

    def _add_file_log(self, file_name):
        file_formatter = logging.Formatter(self._file_format)
        file_handler = handlers.TimedRotatingFileHandler(file_name, when=lu_settings.LOG_WHEN)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(self.level)
        self._logger.addHandler(file_handler)

    def logger(self):
        return self._logger


lu_logger = Logger(
    level=lu_settings.LOG_LEVEL,
    console=True,
    dir=lu_settings.LOG_DIR,
    file=lu_settings.LOG_FILE
).logger()
