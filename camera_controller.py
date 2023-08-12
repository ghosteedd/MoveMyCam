try:
    import onvif as _onvif
except ModuleNotFoundError:
    from sys import executable
    from subprocess import check_call, CalledProcessError
    print('Module onvif-zeep not found!')
    try:
        check_call([executable, '-m', 'pip', 'install', 'onvif-zeep'])
    except CalledProcessError:
        print('Module install failed!')
        exit(1)
    print('Please restart script!')
    exit(1)
except Exception as exc:
    print(f'Import onvif failed! ({exc})')
    exit(2)

import logger as _logger


class CameraController:
    _address: str = ''
    _camera: _onvif.ONVIFCamera | None = None
    _ptz_presets_counts: int = 0

    @property
    def ptz_presets_counts(self) -> int:
        return self._ptz_presets_counts

    @staticmethod
    def check_connection(address: str, port: int, username: str, password: str) -> \
            tuple[int, None] | tuple[int, _onvif.ONVIFCamera]:
        if not (isinstance(address, str) and isinstance(port, int) and isinstance(username, str) and
                isinstance(password, str)) or len(address) < 1 or 65535 < port < 1:
            _logger.debug('[CamController->check_connection] Incorrect arguments for check connection')
            return 1, None
        try:
            camera = _onvif.ONVIFCamera(address, port, username, password)
        except Exception as e:
            _logger.error(f'[CameraController->check_connection] Connection to "{address}" failed!')
            _logger.debug(f'[CameraController->check_connection] Error: {e}')
            return 2, None
        try:
            media_profiles = camera.create_media_service().GetProfiles()
        except Exception as e:
            _logger.error(f'[CameraController->check_connection] Auth on "{address}" failed!')
            _logger.debug(f'[CameraController->check_connection] Error: {e}')
            return 3, None
        if len(media_profiles) < 1:
            _logger.error(f'[CameraController->check_connection] Media profiles on "{address}" not found!')
            return 4, None
        return 0, camera

    def __init__(self, address: str, port: int, username: str, password: str):
        connection = self.check_connection(address, port, username, password)
        if connection[0] == 0:
            self._address = address
            self._camera = connection[1]
            self._get_ptz_presets_counts()

    def _get_ptz_presets_counts(self) -> None:
        if self._camera is None:
            _logger.error('[CameraController->_get_ptz_presets_counts] Camera object is None')
            self._ptz_presets_counts = 0
            return None
        try:
            res = self._camera.create_ptz_service().GetNodes()[0]['MaximumNumberOfPresets']
        except Exception as e:
            _logger.error(f'[CameraController->_get_ptz_presets_counts] Getting counts of presets on '
                          f'"{self._address}" failed!')
            _logger.debug(f'[CameraController->_get_ptz_presets_counts] Error: {e}')
            self._ptz_presets_counts = 0
            return None
        if res < 0:
            _logger.debug(f'[CameraController->_get_ptz_presets_counts] Invalid counts value ({res}) on '
                          f'"{self._address}"')
            self._ptz_presets_counts = 0
            return None
        _logger.debug(f'[CameraController->_get_ptz_presets_counts] For "{self._address}" presets counts: {res}')
        self._ptz_presets_counts = res

    def go_to_preset(self, preset_number: int) -> None:
        if self._camera is None:
            _logger.error('[CameraController->go_to_preset] Camera object is None')
            return None
        if self._ptz_presets_counts == 0:
            self._get_ptz_presets_counts()
        if self._ptz_presets_counts < 1:
            _logger.debug(f'[CameraController->go_to_preset] For "{self._address}" presets not found')
            return None
        if preset_number > self._ptz_presets_counts or preset_number < 1:
            _logger.error('[CameraController->go_to_preset] Incorrect preset number!')
            _logger.debug(f'[CameraController->go_to_preset] Preset number: {preset_number}, presets counts: '
                          f'{self._ptz_presets_counts}')
            return None
        try:
            media_service = self._camera.create_media_service()
            ptz_service = self._camera.create_ptz_service()
            request = ptz_service.create_type('GotoPreset')
            request.ProfileToken = media_service.GetProfiles()[0].token
            request.PresetToken = str(preset_number)
            ptz_service.GotoPreset(request)
            _logger.info(f'[CameraController->go_to_preset] Camera "{self._address}" moved to preset '
                         f'{str(preset_number)}')
        except Exception as e:
            _logger.error('[CameraController->go_to_preset] Move camera to preset failed!')
            _logger.debug(f'[CameraController->go_to_preset] Error: {e}')
