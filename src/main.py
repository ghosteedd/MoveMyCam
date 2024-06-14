#!/usr/bin/python3
# -*- coding: utf-8 -*-


import argparse
import sys
import os


try:
    import pystray
except ModuleNotFoundError:
    print('Module pystray not found! Please install required modules from file "requirements.txt"')
    exit(1)
except Exception as exc:
    print(f'Import module pynput failed ({exc})!')
    exit(1)

try:
    import PIL.Image
except ModuleNotFoundError:
    print('Module pillow not found! Please install required modules from file "requirements.txt"')
    exit(1)
except Exception as exc:
    print(f'Import module pynput failed ({exc})!')
    exit(1)


import keyboard_sniffer
import exceptions
import settings
import logger
import GUI


class Tray:
    _ICON_IMAGE_PATH: str = 'resources/icon.png'
    _icon: pystray.Icon | None = None
    _activation_checked: bool = False
    _settings_window_opened: bool = False
    _sniffer: keyboard_sniffer.KeyboardSniffer | None = None

    def __init__(self, config_path: str | None = None, auto_activate: bool = False):
        """
        :param config_path: Configuration file path
        :param auto_activate: Enable keyboard sniffer on start program (script / tray)
        """
        if isinstance(config_path, str):
            config = settings.Settings(config_file_path=config_path)
            try:
                logger.Logger().print_log = True
                if not config.load():
                    logger.Logger().error('Configuration file not loaded!')
            except exceptions.IncorrectArgsError:
                logger.Logger().error('Wrong camera data type (waiting dictionary)!')
                return
            except exceptions.IncorrectData as e:
                logger.Logger().error('Not found or wrong required parameter in camera data!')
                logger.Logger().debug(str(e))
                return
            except ValueError:
                logger.Logger().error('Wrong log level value!')
                return
        logger.Logger().print_log = False
        # PyInstaller special
        if hasattr(sys, '_MEIPASS'):
            self._ICON_IMAGE_PATH = sys._MEIPASS + '/' + self._ICON_IMAGE_PATH
        if not os.path.exists(self._ICON_IMAGE_PATH):
            logger.Logger().error('Tray icon not found!')
            return
        if not os.path.isfile(self._ICON_IMAGE_PATH):
            logger.Logger().error('Tray icon is not a file!')
            return
        menu = pystray.Menu(
            pystray.MenuItem('Activation',
                             action=self._on_clicked_tray_menu,
                             checked=lambda item: self._activation_checked),
            pystray.MenuItem('Settings', action=self._on_clicked_tray_menu),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', action=self._on_clicked_tray_menu)
        )
        self._sniffer = keyboard_sniffer.KeyboardSniffer()
        if auto_activate:
            if self._sniffer.ready:
                if self._sniffer.start():
                    logger.Logger().info('Sniffer started by autorun')
                    self._activation_checked = True
                else:
                    logger.Logger().warning('Sniffer not started by autorun')
            else:
                logger.Logger().warning('Sniffer not ready for start by autorun')
        try:
            self._icon = pystray.Icon('MoveMyCam', PIL.Image.open(self._ICON_IMAGE_PATH), menu=menu)
            self._sniffer.set_tray_icon(self._icon)
            self._icon.run()
        except Exception as e:
            logger.Logger().error(f'Start tray menu failed! ({e})')

    def _on_clicked_tray_menu(self, _, item):
        """
        Buttons click handler
        """
        match str(item):
            case 'Activation':
                if not self._activation_checked:
                    if self._sniffer.ready:
                        if self._sniffer.start():
                            self._activation_checked = True
                            self._icon.notify('Keyboard sniffer is active')
                        else:
                            logger.Logger().warning('Sniffer not started')
                            self._activation_checked = False
                            self._icon.notify('Keyboard sniffer is NOT active')
                    else:
                        self._activation_checked = False
                        logger.Logger().warning('Sniffer not ready for start')
                        self._icon.notify('Keyboard sniffer not ready')
                else:
                    self._activation_checked = False
                    self._sniffer.stop()
                    self._icon.notify('Keyboard sniffer stopped')
            case 'Settings':
                if not self._settings_window_opened:
                    if self._activation_checked:
                        self._sniffer.stop()
                    self._settings_window_opened = True
                    config_gui = GUI.CamerasWindow()
                    if config_gui.settings_updated:
                        self._sniffer.load_configuration()
                    if self._activation_checked:
                        self._sniffer.start()
                    self._settings_window_opened = False
            case 'Exit':
                if self._sniffer is not None:
                    self._activation_checked = False
                    self._sniffer.stop()
                if self._icon is not None:
                    self._icon.stop()
                    self._icon = None
                else:
                    logger.Logger().error('Stopping tray menu loop failed!')
                    exit(3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup ONVIF PTZ cams to preset(s) // '
                                                 'https://github.com/ghosteedd/')
    parser.add_argument('-a', '--auto-activate', action='store_true', dest='auto_activate',
                        help='auto activate sniffing hotkeys')
    parser.add_argument('-c', '--config', type=str, default=None, help='path to the configuration file')
    args = parser.parse_args()
    Tray(args.config, args.auto_activate)
