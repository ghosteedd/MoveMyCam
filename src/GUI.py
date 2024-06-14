# -*- coding: utf-8 -*-


import functools
import copy
import sys
import re


try:
    import tkinter.messagebox as tk_mb
    import tkinter.ttk as ttk
    import tkinter as tk
except ModuleNotFoundError:
    print('tkinter not available!')
    exit(2)

try:
    import pynput
except ModuleNotFoundError:
    print('Module pynput not found! Please install required modules from file "requirements.txt"')
    exit(1)
except Exception as exc:
    print(f'Import module pynput failed ({exc})!')
    exit(1)


import camera_controller
import keyboard_sniffer
import exceptions
import settings
import logger


class _CameraSettingsWindow:
    _address: str | None = None
    _port: int | None = None
    _username: str | None = None
    _password: str | None = None
    _presets_count: int = 0

    @property
    def presets_count(self):
        return self._presets_count

    @property
    def address(self) -> str | None:
        return self._address

    @address.setter
    def address(self, address: str) -> None:
        if not isinstance(address, str):
            raise TypeError('Only string accepted')
        if len(address) < 1:
            raise ValueError('Address cannot be empty')
        self._address = address
        self._ent_address.delete(0, tk.END)
        self._ent_address.insert(0, address)

    @property
    def port(self) -> int | None:
        return self._port

    @port.setter
    def port(self, port: int) -> None:
        if not isinstance(port, int):
            raise TypeError('Only integer accepted')
        if 65535 < port < 1:
            raise ValueError('Wrong port value')
        self._port = port
        self._ent_port.delete(0, tk.END)
        self._ent_port.insert(0, str(port))

    @property
    def username(self) -> str | None:
        return self._username

    @username.setter
    def username(self, username: str) -> None:
        if not isinstance(username, str):
            raise TypeError('Only string accepted')
        self._username = username
        self._ent_username.delete(0, tk.END)
        self._ent_username.insert(0, username)

    @property
    def password(self) -> str | None:
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        if not isinstance(password, str):
            raise TypeError('Only string accepted')
        self._ent_password.delete(0, tk.END)
        self._ent_password.insert(0, password)

    def __init__(self, init_hidden: bool = False):
        self._window = tk.Toplevel()
        self._window.title('ONVIF camera settings')
        self._window.wm_resizable(False, False)
        self._window.grab_set()
        self._window.focus_set()
        self._window.protocol('WM_DELETE_WINDOW', self._on_delete_window)
        try:
            # PyInstaller special
            if hasattr(sys, '_MEIPASS'):
                path = sys._MEIPASS + '/'
            else:
                path = ''
            path += 'resources/icon.ico'
            self._window.iconbitmap(path)
        except Exception as e:
            logger.Logger().warning('Reading icon file for camera settings window failed!')
            logger.Logger().debug(f'Error text: {e}')
        self._lbl_address = tk.Label(self._window, text='Address:')
        self._lbl_port = tk.Label(self._window, text='Port:')
        self._lbl_username = tk.Label(self._window, text='Username:')
        self._lbl_password = tk.Label(self._window, text='Password:')
        port_validator = (self._window.register(lambda val: re.match(r'^\d{0,5}$', val) is not None), '%P')
        self._ent_address = ttk.Entry(self._window, width=18)
        self._ent_port = ttk.Entry(self._window, width=18, validate='key', validatecommand=port_validator)
        self._ent_username = ttk.Entry(self._window, width=18)
        self._ent_password = ttk.Entry(self._window, width=18, show='*')
        self._ent_port.insert(0, '80')
        self._btn_ok = ttk.Button(self._window, text='ok', command=self._on_click_ok)
        self._btn_cancel = ttk.Button(self._window, text='cancel', command=self._on_click_cancel)
        self._ent_password.bind('<Return>', lambda event: self._on_click_ok())
        self._btn_ok.bind('<Return>', lambda event: self._on_click_ok())
        self._btn_cancel.bind('<Return>', lambda event: self._on_click_cancel())
        self._lbl_address.grid(column=0, row=0, ipadx=0, pady=(5, 2), sticky='e')
        self._ent_address.grid(column=1, row=0, columnspan=2, padx=5, pady=(5, 2), sticky='we')
        self._lbl_port.grid(column=0, row=1, ipadx=0, pady=2, sticky='e')
        self._ent_port.grid(column=1, row=1, columnspan=2, padx=5, pady=2, sticky='we')
        self._lbl_username.grid(column=0, row=2, ipadx=0, pady=2, sticky='e')
        self._ent_username.grid(column=1, row=2, columnspan=2, padx=5, pady=2, sticky='we')
        self._lbl_password.grid(column=0, row=3, ipadx=0, pady=2, sticky='e')
        self._ent_password.grid(column=1, row=3, columnspan=2, padx=5, pady=2, sticky='we')
        self._btn_ok.grid(column=1, row=4, padx=0, pady=(2, 5), sticky='e')
        self._btn_cancel.grid(column=2, row=4, padx=(0, 5), pady=(2, 5), sticky='e')
        if init_hidden:
            self._window.withdraw()

    def wait_result(self) -> None:
        self._window.wait_window()

    def show(self) -> None:
        self._window.deiconify()

    def _on_click_ok(self) -> None:
        address = self._ent_address.get()
        port = self._ent_port.get()
        username = self._ent_username.get()
        password = self._ent_password.get()
        if len(address) < 1:
            tk_mb.showerror('Error', 'Address cannot be empty!')
            return None
        try:
            port = int(port)
        except ValueError:
            tk_mb.showerror('Error', 'Wrong port number!')
            return None
        if 62232 < port < 1:
            tk_mb.showerror('Error', 'Port number out of range!')
            return None
        self._address = None
        self._port = None
        self._username = None
        self._password = None
        self._presets_count = 0
        try:
            camera = camera_controller.CameraController(address, port, username, password)
            self._presets_count = camera.ptz_presets_count
        except exceptions.IncorrectArgsError:
            tk_mb.showerror('Test connection failed', 'Wrong camera data!')
            return None
        except exceptions.ConnectionToCameraError as e:
            tk_mb.showerror('Test connection failed',
                            'Connection to host failed! Check entered address/port!')
            logger.Logger().debug(f'Connection to "{address}" failed with error: {str(e)}')
            return None
        except exceptions.GettingProfilesFromCameraError as e:
            tk_mb.showerror('Test connection failed',
                            'Getting media profiles failed! Check entered username/password!')
            logger.Logger().debug(f'Connection to "{address}" failed with error: {str(e)}')
            return None
        except exceptions.NoMediaProfilesOnCameraError:
            tk_mb.showerror('Test connection failed', 'Media profiles not found! Check settings on camera!')
            return None
        except exceptions.GettingPresetsCountError as e:
            tk_mb.showerror('Test connection failed', 'Request presets count failed!')
            logger.Logger().debug(f'Connection to "{address}" failed with error: {str(e)}')
            return None
        except exceptions.IncorrectPresetsCountError:
            tk_mb.showerror('Test connection failed', 'Incorrect answer by camera!')
            return None
        except exceptions.CameraError:
            tk_mb.showerror('Test connection failed', 'Initialize camera object failed!')
            return None
        self._address = address
        self._port = port
        self._username = username
        self._password = password
        self._window.destroy()

    def _on_click_cancel(self) -> None:
        self._address = None
        self._port = None
        self._username = None
        self._password = None
        self._presets_count = 0
        self._window.destroy()

    def _on_delete_window(self) -> None:
        match tk_mb.askyesnocancel(title='Close camera settings', message='Apply settings?'):
            case True:
                self._on_click_ok()
            case False:
                self._on_click_cancel()


class CamerasWindow:
    _hot_key_entries_values: list = list()
    _active_values: list = list()
    _active_checks: list = list()
    _hot_key_entries: list = list()
    _reset_hot_key_buttons: list = list()
    _presets_values: list = list()
    _presets_spins: list = list()
    _key_pressed: list = list()
    _updated_cameras: list = list()
    _selected_entry_hot_key: int | None = None
    _keyboard_listener: pynput.keyboard.Listener | None = None
    _config: settings.Settings = None

    @property
    def settings_updated(self) -> bool:
        return len(self._updated_cameras) != 0

    def __init__(self, start_tk_mainloop: bool = True, init_hidden: bool = False):
        self._hot_key_entries_values.clear()
        self._active_values.clear()
        self._active_checks.clear()
        self._hot_key_entries.clear()
        self._reset_hot_key_buttons.clear()
        self._presets_values.clear()
        self._presets_spins.clear()
        self._updated_cameras.clear()
        self._key_pressed.clear()
        self._window = tk.Tk()
        self._window.title('Settings')
        self._window.resizable(False, False)
        self._window.protocol('WM_DELETE_WINDOW', self._on_delete_window)
        try:
            if hasattr(sys, '_MEIPASS'):
                path = sys._MEIPASS + '/'
            else:
                path = ''
            path += 'resources/icon.ico'
            self._window.iconbitmap(path)
        except Exception as e:
            logger.Logger().warning('Reading icon file for settings window failed!')
            logger.Logger().debug(f' Error text: {e}')
        hot_key_frame = ttk.Frame(self._window)
        hot_key_number = 0
        for column in range(3):
            for row in range(3):
                hot_key_number += 1
                box_hot_key = ttk.LabelFrame(hot_key_frame, text=f'Key {hot_key_number}')
                command = functools.partial(self._on_click_open_onvif_settings, hot_key_number - 1)
                btn_onvif_settings = ttk.Button(box_hot_key, text='Set ONVIF settings',
                                                command=command)
                box_key_sniffer = ttk.LabelFrame(box_hot_key, text='Hot key')
                active = tk.IntVar(value=0)
                ent_value = tk.StringVar(value='')
                command = functools.partial(self._on_click_active_check, hot_key_number - 1)
                chk_activated = ttk.Checkbutton(box_key_sniffer, text='Active', variable=active, command=command,
                                                state=tk.DISABLED)
                ent_hot_key = ttk.Entry(box_key_sniffer, width=12, textvariable=ent_value, state=tk.DISABLED)
                ent_hot_key.bind('<Key>', lambda _: 'break')
                ent_hot_key.bind('<FocusIn>', functools.partial(self._hot_key_focus_in, hot_key_number - 1))
                ent_hot_key.bind('<FocusOut>', self._hot_key_focus_out)
                self._hot_key_entries_values.append(ent_value)
                self._active_values.append(active)
                self._active_checks.append(chk_activated)
                self._hot_key_entries.append(ent_hot_key)
                command = functools.partial(self._on_click_reset_hot_key, hot_key_number - 1)
                btn_reset_key = ttk.Button(box_key_sniffer, text='Reset key', state=tk.DISABLED, command=command)
                self._reset_hot_key_buttons.append(btn_reset_key)
                preset = tk.StringVar(value='1')
                self._presets_values.append(preset)
                lbl_preset = ttk.Label(box_hot_key, text='Preset:')
                num_validator = (self._window.register(lambda val: re.match(r'^\d{0,4}$', val) is not None), '%P')
                command = functools.partial(self._on_change_preset, hot_key_number - 1)
                spb_preset = ttk.Spinbox(box_hot_key, from_=1.0, to=1024.0, increment=1.0, wrap=True, validate='all',
                                         validatecommand=num_validator, command=command, state=tk.DISABLED,
                                         textvariable=preset)
                spb_preset.bind('<KeyRelease>', command)
                self._presets_spins.append(spb_preset)
                btn_onvif_settings.pack(padx=2, pady=2, fill=tk.BOTH)
                chk_activated.pack(padx=2, pady=2, fill=tk.BOTH)
                box_key_sniffer.pack(padx=2, pady=2, fill=tk.BOTH)
                ent_hot_key.pack(padx=2, pady=2, fill=tk.BOTH)
                btn_reset_key.pack(padx=2, pady=2, fill=tk.BOTH)
                lbl_preset.pack(padx=2, pady=2, fill=tk.BOTH)
                spb_preset.pack(padx=2, pady=2, fill=tk.BOTH)
                box_hot_key.grid(column=column, row=row, padx=2, pady=2)
        btn_frame = ttk.Frame(self._window)
        btn_ok = ttk.Button(btn_frame, text='ok', command=self._on_click_ok)
        btn_cancel = ttk.Button(btn_frame, text='cancel', command=self._on_click_cancel)
        btn_ok.bind('<Return>', lambda event: self._on_click_ok())
        btn_cancel.bind('<Return>', lambda event: self._on_click_cancel())
        btn_cancel.pack(side=tk.RIGHT, padx=2, pady=2)
        btn_ok.pack(side=tk.RIGHT, padx=2, pady=2)
        hot_key_frame.pack(padx=2, pady=2)
        btn_frame.pack(padx=2, pady=2, anchor='se')
        self._config = settings.Settings()
        if isinstance(self._config.data, settings.SettingsData):
            if isinstance(self._config.data.cameras, list):
                for i in range(9):
                    item = self._config.get_camera(i + 1)
                    if item is None:
                        self._hot_key_entries_values[i].set('')
                        self._presets_spins[i]['to'] = 1.0
                        self._presets_values[i].set('1')
                        self._active_checks[i]['state'] = tk.DISABLED
                        self._hot_key_entries[i]['state'] = tk.DISABLED
                        self._reset_hot_key_buttons[i]['state'] = tk.DISABLED
                        self._presets_spins[i]['state'] = tk.DISABLED
                        continue
                    if item.activated:
                        self._active_values[i].set(1)
                    else:
                        self._active_values[i].set(0)
                    first_key = True
                    keys_text = ''
                    for key in item.hot_keys:
                        if not first_key:
                            keys_text += ' + '
                        else:
                            first_key = False
                        keys_text += key
                    self._hot_key_entries_values[i].set(keys_text)
                    self._presets_spins[i]['to'] = float(item.max_count)
                    self._presets_values[i].set(str(item.preset))
                    self._active_checks[i]['state'] = tk.ACTIVE
                    self._hot_key_entries[i]['state'] = tk.ACTIVE
                    self._reset_hot_key_buttons[i]['state'] = tk.ACTIVE
                    self._presets_spins[i]['state'] = tk.ACTIVE
        if start_tk_mainloop:
            self._window.after(100, lambda: self._window.focus_force())
            self._window.mainloop()
        if init_hidden:
            self._window.withdraw()

    def wait_result(self) -> None:
        self._window.wait_window()

    def show(self) -> None:
        self._window.deiconify()

    def _on_click_open_onvif_settings(self, key_number: int) -> None:
        item = None
        for camera in self._updated_cameras:
            if camera.number == key_number + 1:
                item = camera
                break
        if item is None:
            if not isinstance(self._config.data, settings.SettingsData):
                item = None
            elif not isinstance(self._config.data.cameras, list):
                item = None
            else:
                item = self._config.get_camera(key_number + 1)
        onvif_window = _CameraSettingsWindow()
        if item is not None:
            onvif_window.address = item.address
            onvif_window.port = item.port
            onvif_window.username = item.username
            onvif_window.password = item.password
        else:
            item = settings.CameraData(number=0, activated=True, hot_keys=list(), address='', port=1, username='',
                                       password='', max_count=1, preset=1)
        onvif_window.wait_result()
        if onvif_window.address is None or onvif_window.port is None or \
                onvif_window.username is None or onvif_window.password is None:
            return None
        item.number = key_number + 1
        item.address = onvif_window.address
        item.port = onvif_window.port
        item.username = onvif_window.username
        item.password = onvif_window.password
        item.max_count = onvif_window.presets_count
        if item.max_count > 1024:
            item.max_count = 1024
        if item.max_count < 1:
            return None
        if item.preset > item.max_count or item.preset < 1:
            item.preset = 1
        for camera in self._updated_cameras:
            if camera.number == key_number + 1:
                self._updated_cameras.remove(camera)
                break
        self._updated_cameras.append(item)
        self._active_checks[key_number]['state'] = tk.ACTIVE
        self._active_values[key_number].set(1)
        self._hot_key_entries[key_number]['state'] = tk.ACTIVE
        self._reset_hot_key_buttons[key_number]['state'] = tk.ACTIVE
        self._presets_spins[key_number]['to'] = float(item.max_count)
        self._presets_spins[key_number]['state'] = tk.ACTIVE
        self._presets_values[key_number].set(str(item.preset))

    def _on_click_reset_hot_key(self, key_number: int) -> None:
        if 0 > key_number > len(self._hot_key_entries):
            return None
        if not tk_mb.askyesno(title='Reset hot keys', message='You sure?'):
            return None
        self._hot_key_entries_values[key_number].set('')
        key_number = key_number + 1
        updated = False
        for camera in self._updated_cameras:
            if camera.number == key_number:
                camera.hot_keys = list()
                updated = True
                break
        if not updated:
            camera = self._config.get_camera(key_number)
            if camera is not None:
                camera.hot_keys = list()
                self._updated_cameras.append(camera)

    def _hot_key_focus_in(self, index: int, _) -> None:
        self._selected_entry_hot_key = index
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
        self._keyboard_listener = pynput.keyboard.Listener(on_press=self._key_press, on_release=self._key_release)
        self._keyboard_listener.daemon = True
        self._keyboard_listener.start()

    def _hot_key_focus_out(self, _) -> None:
        self._selected_entry_hot_key = None
        self._key_pressed.clear()
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def _key_press(self, key: pynput.keyboard.Key) -> None:
        key_text = keyboard_sniffer.KeyboardSniffer.key_to_text(key)
        if key_text is None:
            return None
        if key_text in self._key_pressed:
            return None
        if self._selected_entry_hot_key is None:
            return None
        self._key_pressed.append(key_text)
        keys_text_value = ''
        first_key = True
        for key in self._key_pressed:
            if first_key:
                first_key = False
            else:
                keys_text_value += ' + '
            keys_text_value += key
        self._hot_key_entries_values[self._selected_entry_hot_key].set(keys_text_value)
        camera_number = self._selected_entry_hot_key + 1
        updated = False
        for camera in self._updated_cameras:
            if camera.number == camera_number:
                camera.hot_keys = copy.deepcopy(self._key_pressed)
                updated = True
                break
        if not updated:
            camera = self._config.get_camera(camera_number)
            if camera is not None:
                camera.hot_keys = copy.deepcopy(self._key_pressed)
                self._updated_cameras.append(camera)

    def _key_release(self, key: pynput.keyboard.Key) -> None:
        key_text = keyboard_sniffer.KeyboardSniffer.key_to_text(key)
        if key_text is not None and key_text in self._key_pressed:
            self._key_pressed.remove(key_text)

    def _on_click_active_check(self, index: int) -> None:
        new_state = self._active_values[index].get() == 1
        camera_number = index + 1
        updated = False
        for camera in self._updated_cameras:
            if camera.number == camera_number:
                camera.activated = new_state
                updated = True
                break
        if not updated:
            camera = self._config.get_camera(camera_number)
            if camera is not None:
                camera.activated = new_state
                self._updated_cameras.append(camera)

    def _on_change_preset(self, index: int, _=None) -> None:
        preset = self._presets_values[index].get()
        if preset != '':
            preset = int(preset)
        else:
            return None
        camera_number = index + 1
        updated = False
        for camera in self._updated_cameras:
            if camera.number == camera_number:
                if camera.max_count >= preset > 0:
                    camera.preset = preset
                else:
                    camera.preset = camera.max_count
                    self._presets_values[index].set(str(camera.max_count))
                updated = True
                break
        if not updated:
            camera = self._config.get_camera(camera_number)
            if camera is not None:
                if camera.max_count <= preset and preset > 0:
                    camera.preset = preset
                    self._updated_cameras.append(camera)

    def _on_click_ok(self) -> None:
        for camera in self._updated_cameras:
            try:
                self._config.insert_camera(camera, replace=True)
            except exceptions.IncorrectData as e:
                tk_mb.showerror('Error', 'Saving cameras data failed! (incorrect data)')
                logger.Logger().debug(f'Insert camera failed with error: {str(e)}')
                return None
            except exceptions.IncorrectArgsError:
                tk_mb.showerror('Error', 'Saving cameras data failed! (incorrect data type)')
                return None
        try:
            if self._config.save():
                self._settings_updated = True
                self._window.destroy()
            else:
                tk_mb.showerror('Error', 'Saving cameras data failed!')
                return None
        except exceptions.IncorrectData as e:
            tk_mb.showerror('Error', 'Saving cameras data failed! (incorrect data)')
            logger.Logger().debug(f'Save cameras data failed with error: {str(e)}')
            return None

    def _on_click_cancel(self) -> None:
        self._updated_cameras.clear()
        self._window.destroy()

    def _on_delete_window(self) -> None:
        match tk_mb.askyesnocancel(title='Close settings', message='Apply changes?'):
            case True:
                self._on_click_ok()
            case False:
                self._on_click_cancel()
