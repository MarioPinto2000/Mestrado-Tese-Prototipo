from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class AudioController:
    def __init__(self):
        # Obtém o dispositivo de áudio de saída padrão
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

    def get_volume(self):
        # Retorna volume de 0 a 100
        return self.volume.GetMasterVolumeLevelScalar() * 100

    def set_volume(self, value):
        # Define volume de 0 a 100
        self.volume.SetMasterVolumeLevelScalar(value / 100, None)