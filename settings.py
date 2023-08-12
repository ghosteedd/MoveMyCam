from dataclasses import dataclass as _dataclass
from copy import deepcopy as _deepcopy
import base64 as _base64
import json as _json
import os as _os

import keyboard_sniffer as _keyboard_sniffer
import logger as _logger


@_dataclass
class DataElement:
    number: int
    activated: bool
    hot_key: str
    address: str
    port: int
    username: str
    password: str
    max_count: int
    preset: int

    def convert_to_dict(self) -> dict:
        return {'number': self.number,
                'activated': self.activated,
                'hot-key': self.hot_key,
                'address': self.address,
                'port': self.port,
                'username': self.username,
                'password': _base64.b64encode(self.password.encode('UTF-8')).decode('UTF-8'),
                'max-count': self.max_count,
                'preset': self.preset
                }

    @staticmethod
    def data_from_dict(data: dict):
        if not isinstance(data, dict):
            return None
        if not (isinstance(data.get('number'), int) and
                isinstance(data.get('activated'), bool) and
                isinstance(data.get('hot-key'), str) and
                isinstance(data.get('address'), str) and
                isinstance(data.get('port'), int) and
                isinstance(data.get('username'), str) and
                isinstance(data.get('password'), str) and
                isinstance(data.get('max-count'), int) and
                isinstance(data.get('preset'), int)):
            return None
        return DataElement(number=data.get('number'),
                           activated=data.get('activated'),
                           hot_key=data.get('hot-key'),
                           address=data.get('address'),
                           port=data.get('port'),
                           username=data.get('username'),
                           password=_base64.b64decode(data.get('password', '').encode('UTF-8')).decode('UTF-8'),
                           max_count=data.get('max-count'),
                           preset=data.get('preset'))


class Settings:
    _DEFAULT_FILE_PATH: str = 'MoveMyCam.conf'
    _file_path: str = ''
    _data: list | None = None

    @property
    def data(self) -> list | None:
        return _deepcopy(self._data)

    @staticmethod
    def struct_corrected(data: list) -> bool:
        if not isinstance(data, list):
            _logger.debug('[Settings->struct_corrected] Bad settings data struct! Variable is not list')
            return False
        for element in data:
            if not isinstance(element, DataElement):
                _logger.debug('[Settings->struct_corrected] Bad settings data struct! Item in list is not DataElement')
                return False
            if not isinstance(element.number, int):
                _logger.debug('[Settings->struct_corrected] Bad settings data struct! Item number is not integer')
                return False
            if element.number < 0 or element.number >= 10:
                _logger.debug(f'[Settings->struct_corrected] Bad settings data! '
                              f'Incorrect item number ({element.number + 1})')
                return False
            if not isinstance(element.activated, bool):
                _logger.debug(f'[Settings->struct_corrected] Bad settings data struct! '
                              f'Incorrect activated state type for item №{element.number + 1}')
                return False
            if not isinstance(element.hot_key, str):
                _logger.debug(f'[Settings->struct_corrected] Bad settings data struct! '
                              f'Incorrect hot key type for item №{element.number + 1}')
                return False
            if element.hot_key != '':
                if not _keyboard_sniffer.text_key_found(element.hot_key):
                    _logger.debug(f'[Settings->struct_corrected] Bad settings data! '
                                  f'Incorrect hot key value for item №{element.number + 1}')
                    return False
            if not isinstance(element.address, str):
                _logger.debug(f'[Settings->struct_corrected] Bad settings data struct! '
                              f'Incorrect address type for item №{element.number + 1}')
                return False
            if element.address == '':
                _logger.debug(f'[Settings->struct_corrected] Bad settings data! '
                              f'Address cannot be empty (item №{element.number + 1})')
                return False
            if not isinstance(element.port, int):
                _logger.debug(f'[Settings->struct_corrected] Bad settings data struct! '
                              f'Incorrect port type for item №{element.number + 1}')
                return False
            if 65535 < element.port < 1:
                _logger.debug(f'[Settings->struct_corrected] Bad settings data! '
                              f'Incorrect port value for item №{element.number + 1}')
                return False
            if not isinstance(element.username, str):
                _logger.debug(f'[Settings->struct_corrected] Bad settings data struct! '
                              f'Incorrect username type for item №{element.number + 1}')
                return False
            if not isinstance(element.password, str):
                _logger.debug(f'[Settings->struct_corrected] Bad settings data struct! '
                              f'Incorrect password type for item №{element.number + 1}')
                return False
            if not isinstance(element.max_count, int):
                _logger.debug(f'[Settings->struct_corrected] Bad settings data struct! '
                              f'Incorrect max count type for item №{element.number + 1}')
                return False
            if element.max_count < 0:
                _logger.debug(f'[Settings->struct_corrected] Bad settings data! '
                              f'Incorrect max count value for item №{element.number + 1}')
                return False
            if not isinstance(element.preset, int):
                _logger.debug(f'[Settings->struct_corrected] Bad settings data struct! '
                              f'Incorrect preset number type for item №{element.number + 1}')
                return False
            if element.preset < 0:
                _logger.debug(f'[Settings->struct_corrected] Bad settings data! '
                              f'Incorrect preset number for item №{element.number + 1}')
                return False
            if element.preset > element.max_count:
                _logger.debug(f'[Settings->struct_corrected] Bad settings data! '
                              f'Incorrect preset number for item №{element.number + 1}')
                return False
        return True

    def __init__(self, file_path: str | None = None):
        self._data = list()
        if file_path is None:
            self._file_path = self._DEFAULT_FILE_PATH
            return
        else:
            if _os.path.exists(file_path):
                if _os.path.isfile(file_path):
                    self._file_path = file_path
                    return
        _logger.error('[Settings initialize] Set file path failed!')

    def get_element(self, number: int) -> DataElement | None:
        if not isinstance(number, int):
            _logger.debug('[Settings->get_element] Wrong number type')
            return None
        if number < 0 or number >= 10:
            _logger.debug(f'[Settings->get_element] Wrong item number ({number})')
            return None
        if not isinstance(self._data, list):
            _logger.debug('[Settings->get_element] _data is not list')
            return None
        for e in self._data:
            if e.number == number:
                return _deepcopy(e)
        return None

    def insert_element(self, element: DataElement, replace_data: bool = True) -> bool:
        if not isinstance(element, DataElement):
            _logger.debug('[Settings->insert_element] Wrong element type')
            return False
        if not isinstance(self._data, list):
            self._data = list()
        if not self.struct_corrected([element]):
            return False
        for e in self._data:
            if e.number == element.number:
                if replace_data:
                    self._data.remove(e)
                else:
                    _logger.debug(f'[Settings->insert_element] Pre-added item №{e.number + 1} found. '
                                  f'For replace set arg replace_data=True')
                    return False
        self._data.append(element)
        return True

    def remove_element(self, number: int) -> bool:
        if not isinstance(self._data, list):
            _logger.debug('[Settings->remove_element] _data is not list')
            return False
        if not isinstance(number, int):
            _logger.debug('[Settings->remove_element] Wrong number type')
            return False
        if number < 0 or number >= 10:
            _logger.debug(f'[Settings->remove_element] Wrong item number ({number})')
            return False
        for e in self._data:
            if e.number == number:
                self._data.remove(e)
                return True
        _logger.debug(f'[Settings->remove_element] Item №{number} not found')
        return False

    def clear_data(self) -> None:
        if isinstance(self._data, list):
            self._data.clear()
        else:
            self._data = list()

    def save_data(self) -> bool:
        if not isinstance(self._data, list):
            _logger.error('[Settings->save_data] Saving settings failed! Wrong data type')
            return False
        if len(self._data) == 0:
            _logger.error('[Settings->save_data] Saving settings failed! Settings data is empty')
            return False
        if not self.struct_corrected(self._data):
            _logger.error('[Settings->save_data] Saving settings failed! Wrong settings data')
            return False
        save_list = list()
        for elem in self._data:
            save_list.append(elem.convert_to_dict())
        try:
            with open(self._file_path, 'w', encoding='UTF-8') as f:
                _json.dump(save_list, f)
                _logger.debug('[Settings->save_data] Settings file updated')
        except Exception as e:
            _logger.error('[Settings->save_data] Saving settings file failed!')
            _logger.debug(f'[Settings->save_data] Error: {e}')
            return False
        return True

    def load_data(self) -> bool:
        try:
            with open(self._file_path, 'r', encoding='UTF-8') as f:
                dict_data = _json.load(f)
        except Exception as e:
            _logger.error('[Settings->load_data] Reading settings file failed!')
            _logger.debug(f'[Settings->load_data] Error: {e}')
            return False
        data = list()
        for elem in dict_data:
            e = DataElement.data_from_dict(elem)
            if e is None:
                _logger.error('[Settings->load_data] Wrong data in settings file!')
                _logger.debug(f'[Settings->load_data] Wrong element: {str(elem)}')
                return False
            data.append(e)
        if self.struct_corrected(data):
            self._data = data
            _logger.debug('[Settings->load_data] Settings file loaded')
            return True
        else:
            self._data = list()
            _logger.error('[Settings->load_data] Settings file struct not correct!')
            return False
