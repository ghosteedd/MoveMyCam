# -*- coding: utf-8 -*-


"""
Yes, I'm know about logging module. If you like logger - use it. I don't like logger, so I wrote my logger.
"""


import datetime
import enum
import os


try:
    import syslog
    _SYSLOG_AVAILABLE = True
except ModuleNotFoundError:
    _SYSLOG_AVAILABLE = False


class LogLevel(enum.Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    DISABLE_LOG = 5


class Logger:
    __instance = None
    __initialized = False

    _DEFAULT_FILE_PATH = 'MoveMyCam.log'

    _current_log_level: LogLevel = LogLevel.INFO
    _printer: bool = False
    _force_use_file_log: bool = False
    _file_path: str | None = None

    @property
    def log_level(self) -> LogLevel:
        return self._current_log_level

    @log_level.setter
    def log_level(self, value: LogLevel) -> None:
        if isinstance(value, LogLevel):
            self._current_log_level = value

    @property
    def print_log(self) -> bool:
        return self._printer

    @print_log.setter
    def print_log(self, value: bool) -> None:
        if isinstance(value, bool):
            self._printer = value

    @property
    def file_path(self) -> str | None:
        return self._file_path

    @file_path.setter
    def file_path(self, value: str) -> None:
        if not isinstance(value, str) or len(value) < 1:
            return
        if os.path.exists(value):
            if os.path.isdir(value):
                return
            else:
                try:
                    fp = open(value, 'a')
                    fp.close()
                    self._file_path = value
                except IOError:
                    return
        else:
            try:
                fp = open(value, 'w')
                fp.close()
                os.remove(value)
                self._file_path = value
            except IOError:
                return

    @property
    def force_use_file_log(self) -> bool:
        return self._force_use_file_log

    @force_use_file_log.setter
    def force_use_file_log(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        if self._file_path is None and value:
            self._init_file_path()
        self._force_use_file_log = value

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__initialized = False
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, log_level: LogLevel = LogLevel.INFO, print_log: bool = False, force_use_file_log: bool = False,
                 file_path: str = None):
        if self.__initialized:
            return
        self.__initialized = True
        if not isinstance(log_level, LogLevel) or not isinstance(print_log, bool) or \
                not isinstance(force_use_file_log, bool) or not (isinstance(file_path, str) or file_path is None):
            self.log_level = LogLevel.DISABLE_LOG
            self.print_log = False
            self.force_use_file_log = False
            if not _SYSLOG_AVAILABLE:
                self._init_file_path()
            return
        self._current_log_level = log_level
        self._printer = print_log
        if file_path is not None:
            self.file_path = file_path
        if not _SYSLOG_AVAILABLE or force_use_file_log:
            self._init_file_path()
        self.force_use_file_log = force_use_file_log

    def _init_file_path(self) -> None:
        if self._file_path is None:
            self._file_path = self._DEFAULT_FILE_PATH
        if os.path.exists(self._file_path):
            try:
                fp = open(self._file_path, 'a')
                fp.close()
            except IOError:
                self._file_path = None
        else:
            try:
                fp = open(self._file_path, 'w')
                fp.close()
                os.remove(self._file_path)
            except IOError:
                self._file_path = None

    def _add_log_record(self, log_level: LogLevel, text: str) -> bool:

        def to_syslog() -> None:
            syslog_priority = None
            match log_level:
                case LogLevel.DEBUG:
                    syslog_priority = syslog.LOG_DEBUG
                case LogLevel.INFO:
                    syslog_priority = syslog.LOG_INFO
                case LogLevel.WARNING:
                    syslog_priority = syslog.LOG_WARNING
                case LogLevel.ERROR:
                    syslog_priority = syslog.LOG_ERR
                case LogLevel.CRITICAL:
                    syslog_priority = syslog.LOG_CRIT
            if syslog_priority is None:
                return None
            syslog.syslog(syslog_priority, text)

        def get_text_prefix() -> str:
            match log_level:
                case LogLevel.DEBUG:
                    return 'DEBUG'
                case LogLevel.INFO:
                    return 'INFO'
                case LogLevel.WARNING:
                    return 'WARNING'
                case LogLevel.ERROR:
                    return 'ERROR'
                case LogLevel.CRITICAL:
                    return 'CRITICAL'
            return 'UNKNOWN'

        def to_file() -> bool:
            timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            try:
                with open(self._file_path, 'a', encoding='UTF-8') as f:
                    f.write(timestamp + ' :: ' + get_text_prefix() + ' :: ' + text + '\n')
                return True
            except IOError:
                return False

        def to_console() -> None:
            timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            print(timestamp + ' :: ' + get_text_prefix() + ' :: ' + text + '\n')

        if not isinstance(text, str) or len(text) < 1:
            return False
        if log_level.value < self._current_log_level.value:
            return False
        if self._printer:
            to_console()
        if _SYSLOG_AVAILABLE and not self._force_use_file_log:
            to_syslog()
            return True
        if self._file_path is None:
            return False
        return to_file()

    def debug(self, text: str) -> bool:
        return self._add_log_record(LogLevel.DEBUG, text)

    def info(self, text: str) -> bool:
        return self._add_log_record(LogLevel.INFO, text)

    def warning(self, text: str) -> bool:
        return self._add_log_record(LogLevel.WARNING, text)

    def error(self, text: str) -> bool:
        return self._add_log_record(LogLevel.ERROR, text)

    def critical(self, text: str) -> bool:
        return self._add_log_record(LogLevel.CRITICAL, text)
