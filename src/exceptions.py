# -*- coding: utf-8 -*-


class IncorrectArgsError(Exception):
    pass


class CameraError(Exception):
    pass


class ConnectionToCameraError(CameraError):
    pass


class GettingProfilesFromCameraError(CameraError):
    pass


class NoMediaProfilesOnCameraError(CameraError):
    pass


class GettingPresetsCountError(CameraError):
    pass


class IncorrectPresetsCountError(CameraError):
    pass


class CameraMoveError(CameraError):
    pass


class IncorrectData(Exception):
    pass


class GuiError(Exception):
    pass
