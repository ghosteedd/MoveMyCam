try:
    import syslog as _syslog
    _SYSLOG_AVAILABLE = True
except ModuleNotFoundError:
    import datetime as _datetime

    _SYSLOG_AVAILABLE = False

# -1 - disable log
# 0 - only errors
# 1 - errors and warnings
# 2 - errors, warnings and info
# 3- errors, warnings, info and debug information
log_level = -1
# Set True for print log to console
print_log = False
# Used if syslog is not available
log_file_path = 'MoveMyCam.log'


def _save_log_to_file(text: str, log_prefix: str) -> None:
    if not isinstance(text, str) or len(text) == 0 or not isinstance(log_prefix, str) or len(log_prefix) == 0:
        return None
    time_stamp = _datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    try:
        with open(log_file_path, 'a', encoding='UTF-8') as f:
            f.write(time_stamp + ' :: ' + log_prefix + ' :: ' + text + '\n')
    except Exception as e:
        print(f'Saving log information failed! ({e})')


def debug(text: str) -> None:
    if log_level < 3:
        return None
    if not isinstance(text, str) or len(text) == 0:
        return None
    if print_log:
        print('DEBUG:: ' + text)
    if _SYSLOG_AVAILABLE:
        _syslog.syslog(_syslog.LOG_DEBUG, text)
    else:
        _save_log_to_file(text, 'DEBUG')


def info(text: str) -> None:
    if log_level < 2:
        return None
    if not isinstance(text, str) or len(text) == 0:
        return None
    if print_log:
        print('INFO:: ' + text)
    if _SYSLOG_AVAILABLE:
        _syslog.syslog(_syslog.LOG_INFO, text)
    else:
        _save_log_to_file(text, 'INFO')


def warning(text: str) -> None:
    if log_level < 1:
        return None
    if not isinstance(text, str) or len(text) == 0:
        return None
    if print_log:
        print('WARNING:: ' + text)
    if _SYSLOG_AVAILABLE:
        _syslog.syslog(_syslog.LOG_WARNING, text)
    else:
        _save_log_to_file(text, 'WARNING')


def error(text: str) -> None:
    if log_level < 0:
        return None
    if not isinstance(text, str) or len(text) == 0:
        return None
    if print_log:
        print('ERROR::' + text)
    if _SYSLOG_AVAILABLE:
        _syslog.syslog(_syslog.LOG_ERR, text)
    else:
        _save_log_to_file(text, 'ERROR')
