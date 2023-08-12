#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os

try:
    import pystray
except ModuleNotFoundError:
    from subprocess import check_call, CalledProcessError
    print('Module pystray not found!')
    try:
        check_call([sys.executable, '-m', 'pip', 'install', 'pystray'])
    except CalledProcessError:
        print('Module install failed!')
        exit(1)
    print('Please restart script!')
    exit(1)
except Exception as exc:
    print(f'Import pystray failed! ({exc})')
    exit(2)

try:
    import PIL.Image
except ModuleNotFoundError:
    from subprocess import check_call, CalledProcessError
    print('Module pillow not found!')
    try:
        check_call([sys.executable, '-m', 'pip', 'install', 'pillow'])
    except CalledProcessError:
        print('Module install failed!')
        exit(1)
    print('Please restart script!')
    exit(1)

import keyboard_sniffer
import logger
import GUI


class Tray:
    _ICON_IMAGE_PATH: str = 'resources/icon.png'
    _icon: pystray.Icon | None = None
    _activation_checked: bool = False
    _sniffer: keyboard_sniffer.KeyboardSniffer | None = None

    def __init__(self, auto_activate: bool = False):
        if hasattr(sys, '_MEIPASS'):
            self._ICON_IMAGE_PATH = sys._MEIPASS + '/' + self._ICON_IMAGE_PATH
        if not os.path.exists(self._ICON_IMAGE_PATH):
            logger.error('[Tray initialize] Tray icon not found!')
            return
        if not os.path.isfile(self._ICON_IMAGE_PATH):
            logger.error('[Tray initialize] Tray icon is not a file!')
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
                logger.info('[Tray initialize] Sniffer started by autorun')
                self._activation_checked = True
                self._sniffer.start()
            else:
                logger.info('[Tray initialize] Sniffer not ready for start by autorun')
        try:
            self._icon = pystray.Icon('MoveMyCam', PIL.Image.open(self._ICON_IMAGE_PATH), menu=menu)
            self._icon.run()
        except Exception as e:
            logger.error(f'[Tray initialize] Start tray menu failed! ({e})')

    def stop(self):
        if self._sniffer is not None:
            self._activation_checked = False
            self._sniffer.stop()
        if self._icon is not None:
            self._icon.stop()
            self._icon = None
        else:
            logger.error('[Tray->stop] Stopping tray menu loop failed!')

    def _on_clicked_tray_menu(self, _, item):
        match str(item):
            case 'Activation':
                if not self._activation_checked:
                    if self._sniffer.ready:
                        self._activation_checked = True
                        self._sniffer.start()
                    else:
                        self._activation_checked = False
                        logger.warning('[Tray->_on_clicked_tray_menu] Sniffer not ready for start!')
                else:
                    self._activation_checked = False
                    self._sniffer.stop()
            case 'Settings':
                self._icon.visible = False
                if self._activation_checked:
                    self._sniffer.stop()
                conf_gui = GUI.SettingsWindow(load_settings=True)
                if conf_gui.settings_updated:
                    self._sniffer.reload_settings()
                if self._activation_checked:
                    self._sniffer.start()
                self._icon.visible = True
            case 'Exit':
                self.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup ONVIF PTZ cams to preset(s) // '
                                                 'https://github.com/ghosteedd/')
    parser.add_argument('-a', '--auto-activate',
                        action='store_true',
                        dest='auto_activate',
                        help='auto activate sniffing hotkeys'
                        )
    Tray(parser.parse_args().auto_activate)
