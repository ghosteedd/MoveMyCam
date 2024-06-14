# -*- coding: utf-8 -*-


import sys
import os


try:
    import onvif
except ModuleNotFoundError:
    print('Module onvif-zeep not found! Please install required modules from file "requirements.txt"')
    exit(1)
except Exception as exc:
    print(f'Import module onvif-zeep failed ({exc})!')
    exit(1)


import exceptions
import logger


class CameraController:
    _address: str = '0.0.0.0'
    _port: int = 80
    _username: str = 'admin'
    _password: str = 'admin'
    _camera: onvif.ONVIFCamera | None = None
    _ptz_presets_count: int = 0

    @property
    def ptz_presets_count(self) -> int:
        return self._ptz_presets_count

    def __init__(self, address: str, port: int, username: str, password: str):
        """
        :param address: Address of IP camera
        :param port: ONVIF port on IP camera
        :param username: ONVIF username
        :param password: ONVIF user password
        :exception exceptions.IncorrectArgsError: Wrong argument(s) type or value
        :exception exceptions.ConnectionToCameraError: Wrong address or port of camera
        :exception exceptions.GettingProfilesFromCameraError: Getting media profiles failed. Check username and password
        :exception exceptions.NoMediaProfilesOnCameraError: No media profiles on camera
        :exception exceptions.CameraError: Camera not initialized
        :exception exceptions.GettingPresetsCountError: Request for getting count failed
        :exception exceptions.IncorrectPresetsCountError: Incorrect answer by camera (check ONVIF data on camera)
        """
        if not (isinstance(address, str) and isinstance(port, int) and isinstance(username, str) and
                isinstance(password, str)):
            raise exceptions.IncorrectArgsError
        if address == '' or port < 1 or port > 65535:
            raise exceptions.IncorrectArgsError
        self._address = address
        self._port = port
        self._username = username
        self._password = password
        self._init_camera()
        self._get_ptz_presets_count()

    def _init_camera(self) -> None:
        """
        Initialize camera object
        :exception exceptions.ConnectionToCameraError: Wrong address or port of camera
        :exception exceptions.GettingProfilesFromCameraError: Getting media profiles failed. Check username and password
        :exception exceptions.NoMediaProfilesOnCameraError: No media profiles on camera
        """
        wsdl_path = os.path.dirname(os.path.abspath(__file__))
        if hasattr(sys, '_MEIPASS'):
            wsdl_path += '/resources/wsdl'
        else:
            wsdl_path += '/../resources/wsdl'
        self._camera = None
        try:
            camera = onvif.ONVIFCamera(self._address, self._port, self._username, self._password, wsdl_path)
        except Exception as e:
            raise exceptions.ConnectionToCameraError(str(e))
        try:
            media_profiles = camera.create_media_service().GetProfiles()
        except Exception as e:
            raise exceptions.GettingProfilesFromCameraError(str(e))
        if len(media_profiles) < 1:
            raise exceptions.NoMediaProfilesOnCameraError
        self._camera = camera

    def _get_ptz_presets_count(self) -> None:
        """
        Requesting count of PTZ presets on IP camera
        :exception exceptions.GettingPresetsCountError: Request for getting count failed
        :exception exceptions.CameraError: Camera not initialized
        :exception exceptions.IncorrectPresetsCountError: Incorrect answer by camera (checking ONVIF data on camera)
        """
        if self._camera is None:
            raise exceptions.CameraError
        self._ptz_presets_count = 0
        try:
            count = self._camera.create_ptz_service().GetNodes()[0]['MaximumNumberOfPresets']
        except Exception as e:
            raise exceptions.GettingPresetsCountError(str(e))
        if count < 0:
            raise exceptions.IncorrectPresetsCountError
        self._ptz_presets_count = count

    def go_to_preset(self, preset_number: int) -> bool:
        """
        Moving ONVIF camera to new position
        :return: Request status
        :exception exceptions.IncorrectArgsError: Wrong preset number
        :exception exceptions.CameraError: Camera not initialized
        :exception exceptions.GettingPresetsCountError: Request for getting count failed
        :exception exceptions.IncorrectPresetsCountError: Incorrect answer by camera (checking ONVIF data on camera)
        """
        if self._camera is None:
            raise exceptions.CameraError
        if not isinstance(preset_number, int):
            raise exceptions.IncorrectArgsError
        if self._ptz_presets_count == 0:
            self._get_ptz_presets_count()
            if self._ptz_presets_count == 0:
                logger.Logger().info(f'For camera with address "{self._address}" presets not found!')
                return False
        if preset_number > self._ptz_presets_count or preset_number < 1:
            raise exceptions.IncorrectArgsError
        try:
            media_service = self._camera.create_media_service()
            ptz_service = self._camera.create_ptz_service()
            request = ptz_service.create_type('GotoPreset')
            request.ProfileToken = media_service.GetProfiles()[0].token
            request.PresetToken = str(preset_number)
            ptz_service.GotoPreset(request)
            logger.Logger().info(f'Camera with address "{self._address}" moved to preset №{preset_number}')
            return True
        except Exception as e:
            raise exceptions.CameraMoveError(str(e))
