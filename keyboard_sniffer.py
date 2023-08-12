from string import printable as _simbols
import platform as _platform

try:
    import pynput as _pynput
    from pynput.keyboard import Key as _Key
except ModuleNotFoundError:
    from sys import executable
    from subprocess import check_call, CalledProcessError
    print('Module pynput not found!')
    try:
        check_call([executable, '-m', 'pip', 'install', 'pynput'])
    except CalledProcessError:
        print('Module install failed!')
        exit(1)
    print('Please restart script!')
    exit(1)
except Exception as exc:
    print(f'Import pynput failed! ({exc})')
    exit(2)

import camera_controller as _camera_controller
import settings as _settings
import logger as _logger


_KEYS = (
    (_Key.alt, 'ALT'),
    (_Key.alt_r, 'ALT R'),
    (_Key.alt_l, 'ALT L'),
    (_Key.alt_gr, 'ALT GR'),
    (_Key.backspace, 'BACKSPACE'),
    (_Key.caps_lock, 'CAPS LOCK'),
    (_Key.cmd, 'CMD'),
    (_Key.cmd_l, 'CMD L'),
    (_Key.cmd_r, 'CMD R'),
    (_Key.delete, 'DEL'),
    (_Key.down, 'DOWN'),
    (_Key.end, 'END'),
    (_Key.enter, 'ENTER'),
    (_Key.esc, 'ESC'),
    (_Key.f1, 'F1'),
    (_Key.f2, 'F2'),
    (_Key.f3, 'F3'),
    (_Key.f4, 'F4'),
    (_Key.f5, 'F5'),
    (_Key.f6, 'F6'),
    (_Key.f7, 'F7'),
    (_Key.f8, 'F8'),
    (_Key.f9, 'F9'),
    (_Key.f10, 'F10'),
    (_Key.f11, 'F11'),
    (_Key.f12, 'F12'),
    (_Key.f13, 'F13'),
    (_Key.f14, 'F14'),
    (_Key.f15, 'F15'),
    (_Key.f16, 'F16'),
    (_Key.f17, 'F17'),
    (_Key.f18, 'F18'),
    (_Key.f19, 'F19'),
    (_Key.f20, 'F20'),
    (_Key.home, 'HOME'),
    (_Key.page_down, 'PAGE DOWN'),
    (_Key.page_up, 'PAGE UP'),
    (_Key.right, 'RIGHT'),
    (_Key.shift, 'SHIFT'),
    (_Key.shift_l, 'SHIFT L'),
    (_Key.shift_r, 'SHIFT R'),
    (_Key.space, 'SPACE'),
    (_Key.tab, 'TAB'),
    (_Key.up, 'UP'),
    (_Key.media_play_pause, 'PLAY/PAUSE'),
    (_Key.media_volume_mute, 'MUTE'),
    (_Key.media_volume_down, 'VOL DOWN'),
    (_Key.media_volume_up, 'VOL UP'),
    (_Key.media_previous, 'PRE MEDIA'),
    (_Key.media_next, 'NEXT MEDIA'),
    (_Key.insert, 'INSERT'),
    (_Key.menu, 'MENU'),
    (_Key.num_lock, 'NUM LOCK'),
    (_Key.pause, 'PAUSE'),
    (_Key.scroll_lock, 'SCROLL LOCK'),
    (_Key.ctrl, 'CTRL'),
    (_Key.ctrl_l, 'CTRL L'),
    (_Key.ctrl_r, 'CTRL R'),
    (_Key.left, 'LEFT'),
)


_WINDOWS_KEYS = (
    (96, 'NUM 0'),
    (97, 'NUM 1'),
    (98, 'NUM 2'),
    (99, 'NUM 3'),
    (100, 'NUM 4'),
    (101, 'NUM 5'),
    (102, 'NUM 6'),
    (103, 'NUM 7'),
    (104, 'NUM 8'),
    (105, 'NUM 9'),
)


def text_key_found(key_text: str) -> bool:
    if not isinstance(key_text, str):
        return False
    key_text = key_text.upper()
    for k in _KEYS:
        if k[1] == key_text:
            return True
    if _platform.system() == 'Windows':
        for k in _WINDOWS_KEYS:
            if k[1] == key_text:
                return True
    if key_text in _simbols and len(key_text) == 1:
        return True
    return False


def key_to_text(key: _pynput.keyboard.Key) -> str | None:
    try:
        return key.char.upper()
    except AttributeError:
        for i in _KEYS:
            if key == i[0]:
                return i[1]
        if hasattr(key, 'vk'):
            for i in _WINDOWS_KEYS:
                if key.vk == i[0]:
                    return i[1]
        return None


class KeyboardSniffer:
    _keyboard_listener: _pynput.keyboard.Listener | None = None
    _config: list | None = None
    _hot_keys: list | None = None

    @property
    def ready(self) -> bool:
        if self._config is None:
            return False
        if len(self._config) == 0:
            return False
        return True

    def __init__(self, auto_load_settings: bool = True, auto_start: bool = False):
        if auto_load_settings:
            self.load_settings()
        if auto_start:
            self.start()

    def start(self) -> bool:
        if self._config is None or len(self._config) == 0:
            _logger.error('[KeyboardSniffer->start] Sniffer not started! Settings list empty')
            return False
        if isinstance(self._keyboard_listener, _pynput.keyboard.Listener):
            self._keyboard_listener.stop()
        self._keyboard_listener = _pynput.keyboard.Listener(on_release=self._key_release)
        self._keyboard_listener.daemon = True
        self._keyboard_listener.start()
        _logger.info('[KeyboardSniffer->start] Sniffer started')
        return self._keyboard_listener.is_alive()

    def stop(self) -> None:
        if self._keyboard_listener is None:
            _logger.info('[KeyboardSniffer->stop] Sniffer not started')
            return None
        if self._keyboard_listener.is_alive():
            self._keyboard_listener.stop()
        self._keyboard_listener = None
        _logger.info('[KeyboardSniffer->stop] Sniffer stopped')

    def reload_settings(self) -> bool:
        return self.load_settings()

    def load_settings(self) -> bool:
        before_worked = False
        if self._keyboard_listener is not None:
            before_worked = self._keyboard_listener.is_alive()
            if before_worked:
                self._keyboard_listener.stop()
        self._config = None
        self._hot_keys = None
        settings = _settings.Settings()
        if not settings.load_data():
            return False
        self._config = settings.data
        self._hot_keys = list()
        for elem in self._config:
            self._hot_keys.append(elem.hot_key)
        if len(self._hot_keys) == 0:
            return False
        if before_worked:
            self._keyboard_listener = _pynput.keyboard.Listener(on_release=self._key_release)
            self._keyboard_listener.daemon = True
            self._keyboard_listener.start()
        return True

    def _key_release(self, key: _pynput.keyboard.Key) -> None:
        if not (isinstance(self._config, list) and isinstance(self._hot_keys, list)):
            return None
        key_text = key_to_text(key)
        if key_text not in self._hot_keys:
            return None
        for item in self._config:
            if not item.activated or item.hot_key == '':
                continue
            if item.hot_key == key_text:
                controller = _camera_controller.CameraController(item.address,
                                                                 item.port,
                                                                 item.username,
                                                                 item.password)
                controller.go_to_preset(item.preset)
