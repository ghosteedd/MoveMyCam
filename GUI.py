import functools as _functools
import sys as _sys
import re as _re

try:
    import tkinter.messagebox as _mb
    import tkinter.ttk as _ttk
    import tkinter as _tk
except ModuleNotFoundError:
    print('Tkinter not available!')
    exit(2)

try:
    import pynput as _pynput
except ModuleNotFoundError:
    from subprocess import check_call, CalledProcessError
    print('Module pynput not found!')
    try:
        check_call([_sys.executable, '-m', 'pip', 'install', 'pynput'])
    except CalledProcessError:
        print('Module install failed!')
        exit(1)
    print('Please restart script!')
    exit(1)
except Exception as exc:
    print(f'Import pynput failed! ({exc})')
    exit(2)

import camera_controller as _camera_controller
import keyboard_sniffer as _keyboard_sniffer
import settings as _settings
import logger as _logger


class CameraSettingsWindow:
    _address: str | None = None
    _port: int | None = None
    _username: str | None = None
    _password: str | None = None

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
        self._ent_address.delete(0, _tk.END)
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
        self._ent_port.delete(0, _tk.END)
        self._ent_port.insert(0, str(port))

    @property
    def username(self) -> str | None:
        return self._username

    @username.setter
    def username(self, username: str) -> None:
        if not isinstance(username, str):
            raise TypeError('Only string accepted')
        self._username = username
        self._ent_username.delete(0, _tk.END)
        self._ent_username.insert(0, username)

    @property
    def password(self) -> str | None:
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        if not isinstance(password, str):
            raise TypeError('Only string accepted')
        self._ent_password.delete(0, _tk.END)
        self._ent_password.insert(0, password)

    def __init__(self, init_hidden: bool = False):
        self._window = _tk.Toplevel()
        self._window.title('ONVIF camera settings')
        self._window.wm_resizable(False, False)
        self._window.attributes('-topmost', True)
        self._window.grab_set()
        self._window.focus_set()
        self._window.protocol('WM_DELETE_WINDOW', self._on_delete_window)
        try:
            if hasattr(_sys, '_MEIPASS'):
                path = _sys._MEIPASS + '/'
            else:
                path = ''
            path += 'resources/icon.ico'
            self._window.iconbitmap(path)
        except Exception as e:
            _logger.warning('[CameraSettingsWindow initialize] Reading icon file failed! Used empty icon')
            _logger.debug(f'[CameraSettingsWindow initialize] Error: {e}')
        self._lbl_address = _tk.Label(self._window, text='Address:')
        self._lbl_port = _tk.Label(self._window, text='Port:')
        self._lbl_username = _tk.Label(self._window, text='Username:')
        self._lbl_password = _tk.Label(self._window, text='Password:')
        port_validator = (self._window.register(lambda val: _re.match(r'^\d{0,5}$', val) is not None), '%P')
        self._ent_address = _ttk.Entry(self._window, width=18)
        self._ent_port = _ttk.Entry(self._window, width=18, validate='key', validatecommand=port_validator)
        self._ent_username = _ttk.Entry(self._window, width=18)
        self._ent_password = _ttk.Entry(self._window, width=18, show='*')
        self._ent_port.insert(0, '80')
        self._btn_ok = _ttk.Button(self._window, text='ok', command=self._on_click_ok)
        self._btn_cancel = _ttk.Button(self._window, text='cancel', command=self._on_click_cancel)
        self._ent_password.bind('<Return>', lambda event: self._on_click_ok())
        self._btn_ok.bind('<Return>', lambda event: self._on_click_ok())
        self._btn_cancel.bind('<Return>', lambda event: self._on_click_cancel())
        self._lbl_address.grid(column=0, row=0, ipadx=5, pady=2, sticky='e')
        self._ent_address.grid(column=1, row=0, columnspan=2, ipadx=5, pady=2, sticky='we')
        self._lbl_port.grid(column=0, row=1, ipadx=5, pady=2, sticky='e')
        self._ent_port.grid(column=1, row=1, columnspan=2, ipadx=5, pady=2, sticky='we')
        self._lbl_username.grid(column=0, row=2, ipadx=5, pady=2, sticky='e')
        self._ent_username.grid(column=1, row=2, columnspan=2, ipadx=5, pady=2, sticky='we')
        self._lbl_password.grid(column=0, row=3, ipadx=5, pady=2, sticky='e')
        self._ent_password.grid(column=1, row=3, columnspan=2, ipadx=5, pady=2, sticky='we')
        self._btn_ok.grid(column=1, row=4, ipadx=5, pady=2, sticky='e')
        self._btn_cancel.grid(column=2, row=4, ipadx=5, pady=2, sticky='e')
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
            _mb.showerror('Error', 'Address cannot be empty!')
            _logger.error('[CameraSettingsWindow->_on_click_ok] Test connection on camera settings window failed! '
                          'Empty address')
            return None
        try:
            port = int(port)
        except ValueError:
            _mb.showerror('Error', 'Wrong port number!')
            _logger.debug('[CameraSettingsWindow->_on_click_ok] Test connection on camera settings window failed! '
                          'Port value in not integer')
            return None
        if 62232 < port < 1:
            _mb.showerror('Error', 'Port number out of range!')
            _logger.error('[CameraSettingsWindow->_on_click_ok] Test connection on camera settings window failed! '
                          'Port number out of range')
            return None
        con = _camera_controller.CameraController.check_connection(address, port, username, password)[0]
        if con == 0:
            self._address = address
            self._port = port
            self._username = username
            self._password = password
            self._window.destroy()
        else:
            self._address = None
            self._port = None
            self._username = None
            self._password = None
            match con:
                case 1:
                    _mb.showinfo('Test connection failed', 'Incorrect information! Check the entered data.')
                case 2:
                    _mb.showerror('Test connection failed', 'Connection to host failed! Check entered address/port.')
                case 3:
                    _mb.showerror('Test connection failed', 'Auth failed! Check entered username/password.')
                case 4:
                    _mb.showerror('Test connection failed', 'Media profiles not found! Check camera settings.')

    def _on_click_cancel(self) -> None:
        self._address = None
        self._port = None
        self._username = None
        self._password = None
        self._window.destroy()

    def _on_delete_window(self) -> None:
        match _mb.askyesnocancel(title='Close camera settings', message='Apply settings?'):
            case True:
                self._on_click_ok()
            case False:
                self._on_click_cancel()


class SettingsWindow:
    _hot_key_entries_values: list = list()
    _hot_key_entries: list = list()
    _reset_hot_key_buttons: list = list()
    _active_values: list = list()
    _active_checks: list = list()
    _presets_values: list = list()
    _presets_spins: list = list()

    _settings_updated: bool = False
    _config: _settings.Settings | None = None
    _selected_entry_hot_key: int | None = None
    _keyboard_listener: _pynput.keyboard.Listener | None = None

    @property
    def settings_updated(self) -> bool:
        return self._settings_updated

    def __init__(self,
                 start_tk_mainloop: bool = True,
                 init_hidden: bool = False,
                 load_settings: bool = False):
        self._hot_key_entries_values.clear()
        self._hot_key_entries.clear()
        self._reset_hot_key_buttons.clear()
        self._active_values.clear()
        self._active_checks.clear()
        self._presets_values.clear()
        self._presets_spins.clear()
        self._config = _settings.Settings()
        self._window = _tk.Tk()
        self._window.title('Settings')
        self._window.resizable(False, False)
        self._window.protocol('WM_DELETE_WINDOW', self._on_delete_window)
        try:
            if hasattr(_sys, '_MEIPASS'):
                path = _sys._MEIPASS + '/'
            else:
                path = ''
            path += 'resources/icon.ico'
            self._window.iconbitmap(path)
        except Exception as e:
            _logger.warning('[SettingsWindow initialize] Reading icon file failed! Used empty icon')
            _logger.debug(f'[SettingsWindow initialize]  Error: {e}')
        hot_key_frame = _ttk.Frame(self._window)
        hot_key_number = 0
        for column in range(3):
            for row in range(3):
                hot_key_number += 1
                box_hot_key = _ttk.LabelFrame(hot_key_frame, text=f'Key {hot_key_number}')
                command = _functools.partial(self._on_click_open_onvif_settings, hot_key_number - 1)
                btn_onvif_settings = _ttk.Button(box_hot_key, text='Set ONVIF settings',
                                                 command=command)
                box_key_sniffer = _ttk.LabelFrame(box_hot_key, text='Hot key')
                active = _tk.IntVar(value=0)
                ent_value = _tk.StringVar(value='')
                chk_activated = _ttk.Checkbutton(box_key_sniffer, text='Active', variable=active, state=_tk.DISABLED)
                ent_hot_key = _ttk.Entry(box_key_sniffer, width=12, textvariable=ent_value, state=_tk.DISABLED)
                ent_hot_key.bind('<Key>', lambda _: 'break')
                ent_hot_key.bind('<FocusIn>', _functools.partial(self._hot_key_focus_in, hot_key_number - 1))
                ent_hot_key.bind('<FocusOut>', self._hot_key_focus_out)
                self._hot_key_entries_values.append(ent_value)
                self._active_values.append(active)
                self._active_checks.append(chk_activated)
                self._hot_key_entries.append(ent_hot_key)
                command = _functools.partial(self._on_click_reset_hot_key, hot_key_number - 1)
                btn_reset_key = _ttk.Button(box_key_sniffer, text='Reset key', state=_tk.DISABLED,
                                            command=command)
                self._reset_hot_key_buttons.append(btn_reset_key)
                preset = _tk.StringVar(value='1')
                self._presets_values.append(preset)
                lbl_preset = _ttk.Label(box_hot_key, text='Preset:')
                num_validator = (self._window.register(lambda val: _re.match(r'^\d{0,4}$', val) is not None), '%P')
                spb_preset = _ttk.Spinbox(box_hot_key, from_=1.0, to=1024.0, increment=1.0, wrap=True, validate='all',
                                          validatecommand=num_validator, state=_tk.DISABLED, textvariable=preset)
                self._presets_spins.append(spb_preset)
                btn_onvif_settings.pack(padx=2, pady=2, fill=_tk.BOTH)
                chk_activated.pack(padx=2, pady=2, fill=_tk.BOTH)
                box_key_sniffer.pack(padx=2, pady=2, fill=_tk.BOTH)
                ent_hot_key.pack(padx=2, pady=2, fill=_tk.BOTH)
                btn_reset_key.pack(padx=2, pady=2, fill=_tk.BOTH)
                lbl_preset.pack(padx=2, pady=2, fill=_tk.BOTH)
                spb_preset.pack(padx=2, pady=2, fill=_tk.BOTH)
                box_hot_key.grid(column=column, row=row, padx=2, pady=2)
        btn_frame = _ttk.Frame(self._window)
        btn_ok = _ttk.Button(btn_frame, text='ok', command=self._on_click_ok)
        btn_cancel = _ttk.Button(btn_frame, text='cancel', command=self._on_click_cancel)
        btn_ok.bind('<Return>', lambda event: self._on_click_ok())
        btn_cancel.bind('<Return>', lambda event: self._on_click_cancel())
        btn_cancel.pack(side=_tk.RIGHT, padx=2, pady=2)
        btn_ok.pack(side=_tk.RIGHT, padx=2, pady=2)
        hot_key_frame.pack(padx=2, pady=2)
        btn_frame.pack(padx=2, pady=2, anchor='se')
        if load_settings:
            self._config.clear_data()
            self._config.load_data()
        if self._config.data is None or len(self._config.data) > 0:
            self._update_settings_data()
        if start_tk_mainloop:
            self._window.mainloop()
        if init_hidden:
            self._window.withdraw()

    def wait_result(self) -> None:
        self._window.wait_window()

    def show(self) -> None:
        self._window.deiconify()

    def _update_settings_data(self) -> None:
        for i in range(9):
            item = self._config.get_element(i)
            if item is None:
                self._hot_key_entries_values[i].set('')
                self._presets_spins[i]['to'] = 1.0
                self._presets_values[i].set('1')
                self._active_checks[i]['state'] = _tk.DISABLED
                self._hot_key_entries[i]['state'] = _tk.DISABLED
                self._reset_hot_key_buttons[i]['state'] = _tk.DISABLED
                self._presets_spins[i]['state'] = _tk.DISABLED
                continue
            if item.activated:
                self._active_values[i].set(1)
            else:
                self._active_values[i].set(0)
            self._hot_key_entries_values[i].set(item.hot_key)
            self._presets_spins[i]['to'] = float(item.max_count)
            self._presets_values[i].set(str(item.preset))
            self._active_checks[i]['state'] = _tk.ACTIVE
            self._hot_key_entries[i]['state'] = _tk.ACTIVE
            self._reset_hot_key_buttons[i]['state'] = _tk.ACTIVE
            self._presets_spins[i]['state'] = _tk.ACTIVE

    def _on_click_open_onvif_settings(self, key_number: int) -> None:
        onvif_window = CameraSettingsWindow()
        item = self._config.get_element(key_number)
        if item is not None:
            onvif_window.address = item.address
            onvif_window.port = item.port
            onvif_window.username = item.username
            onvif_window.password = item.password
        onvif_window.wait_result()
        if onvif_window.address is None or onvif_window.port is None or \
           onvif_window.username is None or onvif_window.password is None:
            return None
        item = self._config.get_element(key_number)
        if item is None:
            item = _settings.DataElement(number=0,
                                         activated=True,
                                         hot_key='',
                                         address='',
                                         port=1,
                                         username='',
                                         password='',
                                         max_count=1,
                                         preset=1)
        item.number = key_number
        item.address = onvif_window.address
        item.port = onvif_window.port
        item.username = onvif_window.username
        item.password = onvif_window.password
        item.preset = 1
        item.max_count = _camera_controller.CameraController(address=item.address,
                                                             port=item.port,
                                                             username=item.username,
                                                             password=item.password).ptz_presets_counts
        if item.max_count > 1024:
            item.max_count = 1024
        if item.max_count < 1:
            return None
        self._config.insert_element(element=item, replace_data=True)
        self._active_checks[key_number]['state'] = _tk.ACTIVE
        self._active_values[key_number].set(1)
        self._hot_key_entries[key_number]['state'] = _tk.ACTIVE
        self._reset_hot_key_buttons[key_number]['state'] = _tk.ACTIVE
        self._presets_spins[key_number]['to'] = float(item.max_count)
        self._presets_spins[key_number]['state'] = _tk.ACTIVE
        self._presets_values[key_number].set(str(item.preset))

    def _on_click_reset_hot_key(self, key_number: int) -> None:
        if 0 > key_number > len(self._hot_key_entries):
            return None
        self._hot_key_entries_values[key_number].set('')

    def _hot_key_focus_in(self, index: int, _) -> None:
        self._selected_entry_hot_key = index
        if self._keyboard_listener is None:
            self._keyboard_listener = _pynput.keyboard.Listener(on_release=self._key_release)
            self._keyboard_listener.daemon = True
            self._keyboard_listener.start()

    def _hot_key_focus_out(self, _) -> None:
        self._selected_entry_hot_key = None
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def _on_click_ok(self) -> None:
        for i in range(9):
            item = self._config.get_element(i)
            if item is None:
                continue
            if self._active_values[i].get() == 1:
                item.activated = True
            else:
                item.activated = False
            item.hot_key = self._hot_key_entries_values[i].get()
            item.preset = int(self._presets_values[i].get())
            if item.preset > item.max_count:
                _mb.showerror('Error', f'Incorrect preset number for key {i + 1}')
                return None
            self._config.insert_element(element=item, replace_data=True)
        if not self._config.save_data():
            _logger.error('[SettingsWindow->_on_click_ok] Saving settings failed!')
            _mb.showerror('Error', 'Saving settings failed!')
            self._settings_updated = False
        else:
            self._settings_updated = True
            self._window.destroy()

    def _on_click_cancel(self) -> None:
        self._settings_updated = False
        self._window.destroy()

    def _on_delete_window(self) -> None:
        match _mb.askyesnocancel(title='Close settings', message='Apply changes?'):
            case True:
                self._on_click_ok()
            case False:
                self._on_click_cancel()

    def _key_release(self, key: _pynput.keyboard.Key) -> None:
        key_text = _keyboard_sniffer.key_to_text(key)
        if key_text is not None and self._selected_entry_hot_key is not None:
            self._hot_key_entries_values[self._selected_entry_hot_key].set(key_text)
