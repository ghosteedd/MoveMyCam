# -*- coding: utf-8 -*-


from string import printable as simbols
import platform


try:
    import pynput
    from pynput.keyboard import Key as PynputKey
except ModuleNotFoundError:
    print('Module pynput not found! Please install required modules from file "requirements.txt"')
    exit(1)
except Exception as exc:
    print(f'Import module pynput failed ({exc})!')
    exit(1)
try:
    import pystray
except ModuleNotFoundError:
    print('Module pystray not found! Please install required modules from file "requirements.txt"')
    exit(1)
except Exception as exc:
    print(f'Import module pynput failed ({exc})!')
    exit(1)


import camera_controller
import exceptions
import settings
import logger


_KEYS = (
    (PynputKey.alt, 'ALT'),
    (PynputKey.alt_r, 'ALT R'),
    (PynputKey.alt_l, 'ALT L'),
    (PynputKey.alt_gr, 'ALT GR'),
    (PynputKey.backspace, 'BACKSPACE'),
    (PynputKey.caps_lock, 'CAPS LOCK'),
    (PynputKey.cmd, 'CMD'),
    (PynputKey.cmd_l, 'CMD L'),
    (PynputKey.cmd_r, 'CMD R'),
    (PynputKey.delete, 'DEL'),
    (PynputKey.down, 'DOWN'),
    (PynputKey.end, 'END'),
    (PynputKey.enter, 'ENTER'),
    (PynputKey.esc, 'ESC'),
    (PynputKey.f1, 'F1'),
    (PynputKey.f2, 'F2'),
    (PynputKey.f3, 'F3'),
    (PynputKey.f4, 'F4'),
    (PynputKey.f5, 'F5'),
    (PynputKey.f6, 'F6'),
    (PynputKey.f7, 'F7'),
    (PynputKey.f8, 'F8'),
    (PynputKey.f9, 'F9'),
    (PynputKey.f10, 'F10'),
    (PynputKey.f11, 'F11'),
    (PynputKey.f12, 'F12'),
    (PynputKey.f13, 'F13'),
    (PynputKey.f14, 'F14'),
    (PynputKey.f15, 'F15'),
    (PynputKey.f16, 'F16'),
    (PynputKey.f17, 'F17'),
    (PynputKey.f18, 'F18'),
    (PynputKey.f19, 'F19'),
    (PynputKey.f20, 'F20'),
    (PynputKey.home, 'HOME'),
    (PynputKey.page_down, 'PAGE DOWN'),
    (PynputKey.page_up, 'PAGE UP'),
    (PynputKey.right, 'RIGHT'),
    (PynputKey.shift, 'SHIFT'),
    (PynputKey.shift_l, 'SHIFT L'),
    (PynputKey.shift_r, 'SHIFT R'),
    (PynputKey.space, 'SPACE'),
    (PynputKey.tab, 'TAB'),
    (PynputKey.up, 'UP'),
    (PynputKey.media_play_pause, 'PLAY/PAUSE'),
    (PynputKey.media_volume_mute, 'MUTE'),
    (PynputKey.media_volume_down, 'VOL DOWN'),
    (PynputKey.media_volume_up, 'VOL UP'),
    (PynputKey.media_previous, 'PRE MEDIA'),
    (PynputKey.media_next, 'NEXT MEDIA'),
    (PynputKey.insert, 'INSERT'),
    (PynputKey.menu, 'MENU'),
    (PynputKey.num_lock, 'NUM LOCK'),
    (PynputKey.pause, 'PAUSE'),
    (PynputKey.scroll_lock, 'SCROLL LOCK'),
    (PynputKey.ctrl, 'CTRL'),
    (PynputKey.ctrl_l, 'CTRL L'),
    (PynputKey.ctrl_r, 'CTRL R'),
    (PynputKey.left, 'LEFT'),
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


class KeyboardSniffer:
    _config: settings.Settings = None
    _tray_icon: pystray.Icon | None = None
    _keyboard_listener: pynput.keyboard.Listener | None = None
    _key_pressed: set | None = None

    @staticmethod
    def key_text_exist(key_text: str) -> bool:
        """
        Checking key text for save to configuration file / append to key press list
        :param key_text: key name/text
        """
        if not isinstance(key_text, str):
            return False
        key_text = key_text.upper()
        for k in _KEYS:
            if k[1] == key_text:
                return True
        if platform.system() == 'Windows':
            for k in _WINDOWS_KEYS:
                if k[1] == key_text:
                    return True
        if key_text in simbols and len(key_text) == 1:
            return True
        return False

    @staticmethod
    def key_to_text(key: pynput.keyboard.Key) -> str | None:
        """
        Gey key text from pynput keyboard key object
        :param key: Pynput key object
        :return: Key text or None if key text not found
        """
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

    @property
    def ready(self) -> bool:
        """
        Keyboard sniffer ready for work (checking settings are loaded)
        :return: Ready status
        """
        if self._config.data.cameras is None or len(self._config.data.cameras) == 0:
            return False
        return True

    def __init__(self, autostart: bool = False):
        """
        :param autostart: Start sniffer on initialize object
        """
        self._config = settings.Settings()
        self._key_pressed = set()
        if autostart:
            self.start()

    def start(self) -> bool:
        """
        Start keyboard sniffer
        :return: Sniffer status after start thread
        """
        if not self.ready:
            return False
        self.load_configuration()
        if isinstance(self._keyboard_listener, pynput.keyboard.Listener):
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        self._key_pressed = set()
        self._keyboard_listener = pynput.keyboard.Listener(on_press=self._key_press, on_release=self._key_release)
        self._keyboard_listener.daemon = True
        self._keyboard_listener.start()
        return self._keyboard_listener.is_alive()

    def stop(self) -> None:
        """
        Stop keyboard sniffer
        """
        if self._keyboard_listener is None:
            return None
        if self._keyboard_listener.is_alive():
            self._keyboard_listener.stop()
        self._keyboard_listener = None
        self._key_pressed.clear()

    def load_configuration(self) -> bool:
        """
        (Re-) loading data from configuration file
        :return: Data update status
        """
        before_worked = False
        if self._keyboard_listener is not None:
            before_worked = self._keyboard_listener.is_alive()
            if before_worked:
                self._keyboard_listener.stop()
        try:
            if not self._config.load():
                logger.Logger().error('Configuration file not loaded (keyboard sniffer)!')
        except exceptions.IncorrectArgsError:
            logger.Logger().error('Wrong camera data type (waiting dictionary, keyboard sniffer)!')
            return False
        except exceptions.IncorrectData as e:
            logger.Logger().error('Not found or wrong required parameter in camera data (keyboard sniffer)!')
            logger.Logger().debug(str(e))
            return False
        except ValueError:
            logger.Logger().error('Wrong log level value (keyboard sniffer)!')
            return False
        if not isinstance(self._config.data.cameras, list):
            return False
        if before_worked:
            self._keyboard_listener = pynput.keyboard.Listener(on_press=self._key_press, on_release=self._key_release)
            self._keyboard_listener.daemon = True
            self._keyboard_listener.start()
        return True

    def set_tray_icon(self, icon: pystray.Icon) -> None:
        if isinstance(icon, pystray.Icon):
            self._tray_icon = icon

    def _tray_notify(self, text: str, title: str | None = None) -> None:
        if not isinstance(self._tray_icon, pystray.Icon):
            return None
        self._tray_icon.notify(text, title)

    def _key_press(self, key: pynput.keyboard.Key) -> None:
        """
        Key press handler
        """
        if not isinstance(self._config.data, settings.SettingsData) or \
           not isinstance(self._config.data.cameras, list):
            return None
        text_key = self.key_to_text(key)
        if text_key is None:
            return None
        if text_key in self._key_pressed:
            return None
        self._key_pressed.add(text_key)

    def _key_release(self, key: pynput.keyboard.Key) -> None:
        """
        Key release handler
        """
        key_text = self.key_to_text(key)
        if key_text is None:
            return None
        for camera in self._config.data.cameras:
            if not camera.activated:
                continue
            match = True
            for hot_key in camera.hot_keys:
                if hot_key not in self._key_pressed:
                    match = False
                    break
            if match:
                try:
                    controller = camera_controller.CameraController(camera.address,
                                                                    camera.port,
                                                                    camera.username,
                                                                    camera.password)
                    if controller.go_to_preset(camera.preset):
                        logger.Logger().info(f'Camera with address "{camera.address}" moved to preset №{camera.preset}')
                        self._tray_notify(f'Camera moved to preset №{camera.preset}', f'Camera {camera.address}')
                except exceptions.IncorrectArgsError:
                    logger.Logger().error(f'Camera with address "{camera.address}" not moved to preset '
                                          f'№{camera.preset} (wrong data)')
                    self._tray_notify(f'Camera not moved!', f'Camera {camera.address}')
                    continue
                except exceptions.ConnectionToCameraError:
                    logger.Logger().error(f'Camera with address "{camera.address}" not moved to preset '
                                          f'№{camera.preset} (connection failed)')
                    continue
                except exceptions.GettingProfilesFromCameraError:
                    logger.Logger().error(f'Camera with address "{camera.address}" not moved to preset '
                                          f'№{camera.preset} (wrong username/password)')
                    self._tray_notify(f'Camera not moved! Wrong username/password', f'Camera {camera.address}')
                    continue
                except exceptions.NoMediaProfilesOnCameraError:
                    logger.Logger().error(f'Camera with address "{camera.address}" not moved to preset '
                                          f'№{camera.preset} (no media profiles)')
                    self._tray_notify(f'Camera not moved! No media profiles', f'Camera {camera.address}')
                    continue
                except exceptions.IncorrectPresetsCountError:
                    logger.Logger().error(f'Camera with address "{camera.address}" not moved to preset '
                                          f'№{camera.preset} (incorrect camera answer)')
                    self._tray_notify(f'Camera not moved! Incorrect answer', f'Camera {camera.address}')
                    continue
                except exceptions.GettingPresetsCountError:
                    logger.Logger().error(f'Camera with address "{camera.address}" not moved to preset '
                                          f'№{camera.preset} (request preset count failed)')
                    self._tray_notify(f'Camera not moved! Request preset count failed', f'Camera {camera.address}')
                    continue
                except exceptions.CameraError:
                    logger.Logger().error(f'Camera with address "{camera.address}" not moved to preset '
                                          f'№{camera.preset} (camera not initialized)')
                    self._tray_notify(f'Camera not initialized!', f'Camera {camera.address}')
                    continue
        if key_text in self._key_pressed:
            self._key_pressed.remove(key_text)
