# -*- coding: utf-8 -*-


import dataclasses
import base64
import json
import os


try:
    import syslog
    del syslog
    _SYSLOG_AVAILABLE = True
except ModuleNotFoundError:
    _SYSLOG_AVAILABLE = False


import keyboard_sniffer
import exceptions
import logger


@dataclasses.dataclass
class CameraData:
    number: int
    activated: bool
    hot_keys: list
    address: str
    port: int
    username: str
    password: str
    max_count: int
    preset: int

    def convert_to_dict(self) -> dict:
        """
        Current object to dictionary converter
        :return:  Dictionary with camera data
        :exception exceptions.IncorrectData: Wrong data type or value
        """
        if not isinstance(self.number, int):
            raise exceptions.IncorrectData('Camera number is not integer!')
        if self.number < 0 or self.number > 9:
            raise exceptions.IncorrectData(f'Incorrect camera number value ({self.number})!')
        if not isinstance(self.activated, bool):
            raise exceptions.IncorrectData(f'Incorrect activated state type for camera №{self.number}!')
        if not isinstance(self.hot_keys, list):
            raise exceptions.IncorrectData(f'Incorrect hot keys type for camera №{self.number}!')
        index = 1
        for hot_key in self.hot_keys:
            if not isinstance(hot_key, str):
                raise exceptions.IncorrectData(f'Wrong type of hot key №{index} for camera №{self.number}!')
            if len(hot_key) == 0:
                raise exceptions.IncorrectData(f'Empty hot key №{index} for camera №{self.number}!')
            if not keyboard_sniffer.KeyboardSniffer.key_text_exist(hot_key):
                raise exceptions.IncorrectData(f'Wrong hot key value №{index} for camera №{self.number}!')
            index += 1
        if not isinstance(self.address, str):
            raise exceptions.IncorrectData(f'Incorrect address type for camera №{self.number}')
        if len(self.address) == 0:
            raise exceptions.IncorrectData(f'Bad camera data! Address cannot be empty! (camera №{self.number})')
        if not isinstance(self.port, int):
            raise exceptions.IncorrectData(f'Incorrect port type for camera №{self.number}')
        if 65535 < self.port < 1:
            raise exceptions.IncorrectData(f'Bad camera data! Incorrect port value for camera №{self.number}')
        if not isinstance(self.username, str):
            raise exceptions.IncorrectData(f'Incorrect username type for camera №{self.number}')
        if not isinstance(self.password, str):
            raise exceptions.IncorrectData(f'Incorrect password type for camera №{self.number}')
        if not isinstance(self.max_count, int):
            raise exceptions.IncorrectData(f'Incorrect count type for camera №{self.number}')
        if self.max_count < 0:
            raise exceptions.IncorrectData(f'Incorrect count value for camera №{self.number}')
        if not isinstance(self.preset, int):
            raise exceptions.IncorrectData(f'Incorrect preset number type for camera №{self.number}')
        if self.preset < 1:
            raise exceptions.IncorrectData(f'Incorrect preset number for camera №{self.number}')
        if self.preset > self.max_count:
            raise exceptions.IncorrectData(f'Incorrect preset number for camera №{self.number}')
        return {'number': self.number,
                'activated': self.activated,
                'hot-keys': self.hot_keys,
                'address': self.address,
                'port': self.port,
                'username': self.username,
                'password': base64.b64encode(self.password.encode('UTF-8')).decode('UTF-8'),
                'max-count': self.max_count,
                'preset': self.preset
                }

    @staticmethod
    def from_dict(data: dict):
        """
        Dictionary to CameraData object converter
        :param data: Dictionary with camera data
        :return: CameraData object
        :exception exceptions.IncorrectArgsError: Wrong data type (waiting dict)
        :exception exceptions.IncorrectData: Not found or wrong required parameter
        """
        if not isinstance(data, dict):
            raise exceptions.IncorrectArgsError
        number = data.get('number')
        if not isinstance(number, int):
            raise exceptions.IncorrectData('Not found or wrong type camera number!')
        if number < 0 or number > 9:
            raise exceptions.IncorrectData(f'Incorrect camera number ({number})!')
        if not isinstance(data.get('activated'), bool):
            raise exceptions.IncorrectData(f'Not found or wrong activation state type for camera №{number}!')
        hot_keys = data.get('hot-keys')
        if not isinstance(hot_keys, list):
            raise exceptions.IncorrectData(f'Not found or wrong hot keys type for camera №{number}!')
        index = 1
        for hot_key in hot_keys:
            if not isinstance(hot_key, str):
                raise exceptions.IncorrectData(f'Wrong type of hot key №{index} for camera №{number}!')
            if len(hot_key) == 0:
                raise exceptions.IncorrectData(f'Empty hot key №{index} for camera №{number}!')
            if not keyboard_sniffer.KeyboardSniffer.key_text_exist(hot_key):
                raise exceptions.IncorrectData(f'Wrong hot key №{index} for camera №{number}!')
            index += 1
        if not isinstance(data.get('address'), str):
            raise exceptions.IncorrectData(f'Not found or wrong address type  for camera №{number}!')
        if len(data.get('address')) == 0:
            raise exceptions.IncorrectData(f'Empty address for camera №{number}!')
        if not isinstance(data.get('port'), int):
            raise exceptions.IncorrectData(f'Not found or wrong port type for camera №{number}!')
        if 65535 < data.get('port') < 1:
            raise exceptions.IncorrectData(f'Wrong port value for camera №{number}!')
        if not isinstance(data.get('username'), str):
            raise exceptions.IncorrectData(f'Not found or wrong username type for camera №{number}!')
        if not isinstance(data.get('password'), str):
            raise exceptions.IncorrectData(f'Not found or wrong password type for camera №{number}!')
        try:
            password = base64.b64decode(data.get('password', '').encode('UTF-8')).decode('UTF-8')
        except base64.binascii.Error:
            raise exceptions.IncorrectData(f'Incorrect password hash for camera №{number}')
        if not isinstance(data.get('max-count'), int):
            raise exceptions.IncorrectData(f'Not found or wrong max count type for camera №{number}!')
        if data.get('max-count') < 1:
            raise exceptions.IncorrectData(f' Wrong max count value for camera №{number}')
        if not isinstance(data.get('preset'), int):
            raise exceptions.IncorrectData(f'Not found or wrong preset type for camera №{number}!')
        if data.get('preset') > data.get('max-count') or data.get('preset') < 1:
            raise exceptions.IncorrectData(f'Wrong preset value for camera №{number}')
        return CameraData(number=data.get('number'),
                          activated=data.get('activated'),
                          hot_keys=data.get('hot-keys'),
                          address=data.get('address'),
                          port=data.get('port'),
                          username=data.get('username'),
                          password=password,
                          max_count=data.get('max-count'),
                          preset=data.get('preset')
                          )


@dataclasses.dataclass
class SettingsData:
    cameras: list | None = dataclasses.field(default=None)
    log_level: logger.LogLevel = dataclasses.field(default=logger.LogLevel.DISABLE_LOG)
    log_path: str = dataclasses.field(default='MoveMyCam.log', init=False)

    def convert_to_dict(self):
        cameras_list = list()
        if isinstance(self.cameras, list):
            for camera in self.cameras:
                cameras_list.append(camera.convert_to_dict())
        data = {
            'cameras': cameras_list,
            'log_level': self.log_level.value
        }
        if not _SYSLOG_AVAILABLE:
            data['log_path'] = self.log_path
        return data

    @staticmethod
    def from_dict(data: dict):
        settings_data = SettingsData()
        cameras_list = data.get('cameras', list())
        cameras_list_out = list()
        if not isinstance(cameras_list, list):
            raise exceptions.IncorrectData('Cameras not a list!')
        for camera in cameras_list:
            cameras_list_out.append(CameraData.from_dict(camera))
        settings_data.cameras = cameras_list_out
        settings_data.log_level = logger.LogLevel(int(data.get('log_level', logger.LogLevel.DISABLE_LOG.value)))
        if not _SYSLOG_AVAILABLE:
            settings_data.log_path = data.get('log_path', 'MoveMyCam.conf')
        return settings_data


class Settings:
    __instance = None
    __initialized = False

    _DEFAULT_FILE_PATH: str = 'MoveMyCam.conf'

    _file_path: str = ''
    _data: SettingsData | None = None

    @property
    def data(self) -> SettingsData:
        if self._data is None:
            return SettingsData()
        else:
            return self._data

    @property
    def file_path(self) -> str:
        return self._file_path

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, config_file_path: str | None = None, autoload: bool = True):
        """
        :param config_file_path: Configuration file path
        :param autoload: Load configuration file when object initialize
        :exception exceptions.IncorrectArgsError: Wrong camera data type (waiting dictionary)
        :exception exceptions.IncorrectData: Not found or wrong required parameter in camera data
        """
        if config_file_path is None:
            self._file_path = self._DEFAULT_FILE_PATH
        elif isinstance(config_file_path, str) and len(config_file_path) > 0:
            self._file_path = config_file_path
        else:
            raise exceptions.IncorrectArgsError
        if autoload:
            self.load()

    def get_camera(self, number: int) -> CameraData | None:
        """
        Receiving a camera data by its number
        :param number: Camera number
        :return: CameraData object if camera exists, None - camera not found
        :exception IncorrectArgsError: Wrong camera number type or value
        """
        if not isinstance(number, int):
            raise exceptions.IncorrectArgsError
        if number < 0 or number > 9:
            raise exceptions.IncorrectArgsError
        if not isinstance(self._data, SettingsData):
            return None
        if not isinstance(self._data.cameras, list):
            self._data.cameras = list()
            return None
        for camera in self._data.cameras:
            if camera.number == number:
                return camera
        return None

    def insert_camera(self, camera: CameraData, replace: bool = False) -> bool:
        """
        Insert cameras data to cameras list
        :param camera: CameraData object
        :param replace: Replace cameras data if found camera with current number
        :return: True - cameras data list updated
        :exception exceptions.IncorrectArgsError: Wrong camera data type
        :exception exceptions.IncorrectData: Wrong camera data type or value in cameras data
        """
        if not isinstance(camera, CameraData):
            raise exceptions.IncorrectArgsError
        if not (isinstance(camera.address, str) and isinstance(camera.port, int) and isinstance(camera.address, str) and
                isinstance(camera.username, str) and isinstance(camera.password, str) and isinstance(camera.preset, int)
                and isinstance(camera.max_count, int) and isinstance(camera.activated, bool)):
            raise exceptions.IncorrectArgsError
        if camera.number < 1 or camera.number > 9 or len(camera.address) == 0 or camera.port < 1 or camera.preset < 0 \
                or camera.max_count < camera.preset or camera.port > 65535:
            raise exceptions.IncorrectData
        if not isinstance(self._data, SettingsData):
            self._data = SettingsData()
        if not isinstance(self._data.cameras, list):
            self._data.cameras = list()
        for c in self._data.cameras:
            if camera.number == c.number:
                if replace:
                    self._data.cameras.remove(c)
                else:
                    return False
        self._data.cameras.append(camera)
        return True

    def remove_camera(self, number: int) -> bool:
        """
        Removing camera from cameras list by its number
        :param number: Camera number
        :return: True - camera removed. False - camera not found
        :exception IncorrectArgsError: Wrong camera number type or value
        """
        if not isinstance(number, int):
            raise exceptions.IncorrectArgsError
        if number < 1 or number > 9:
            raise exceptions.IncorrectArgsError
        if not isinstance(self._data, SettingsData):
            return True
        if not isinstance(self._data.cameras, list):
            return True
        for camera in self._data.cameras:
            if camera.number == number:
                self._data.cameras.remove(camera)
                return True
        return False

    def clear_data(self) -> None:
        """
        Clearing camera list
        """
        if not isinstance(self._data, SettingsData):
            return None
        if isinstance(self._data.cameras, list):
            self._data.cameras.clear()
        else:
            self._data.cameras = list()

    def save(self) -> bool:
        """
        Saving configuration file
        :return: True - data saved. False - no data or saving failed
        :exception exceptions.IncorrectData: Wrong one or more camera data type or value in cameras list
        """
        if not isinstance(self._data, SettingsData):
            return False
        if not isinstance(self._data.cameras, list):
            return False
        if len(self._data.cameras) == 0:
            return False
        try:
            with open(self._file_path, 'w', encoding='UTF-8') as f:
                json.dump(self._data.convert_to_dict(), f)
                return True
        except Exception as e:
            logger.Logger().error(f'Configuration file not saved! Exception text: {str(e)}')
            return False

    def load(self) -> bool:
        """
        Load configuration file
        :return: True - data loaded. False - reading configuration file failed
        :exception exceptions.IncorrectArgsError: Wrong camera data type (waiting dictionary)
        :exception exceptions.IncorrectData: Not found or wrong required parameter in camera data
        :exception ValueError: Wrong log level value
        """
        if not os.path.exists(self._file_path):
            logger.Logger().debug('Configuration file not exits')
            return False
        try:
            with open(self._file_path, 'r', encoding='UTF-8') as f:
                dict_data = json.load(f)
        except Exception as e:
            pre_print_state = logger.Logger().print_log
            logger.Logger().print_log = True
            logger.Logger().error('Reading configuration file failed!')
            logger.Logger().debug(f'Exception text: {e}')
            logger.Logger().print_log = pre_print_state
            return False
        self._data = SettingsData.from_dict(dict_data)
        logger.Logger().log_level = self._data.log_level
        if not _SYSLOG_AVAILABLE:
            logger.Logger().file_path = self._data.log_path
        return True
