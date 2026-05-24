from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class AudioController:
    def __init__(self):
        # Obtém o dispositivo de áudio de saída padrão
        devices = AudioUtilities.GetSpeakers()
        
        # A forma correta de ativar a interface de volume no pycaw:
        # Acedemos ao 'Activate' do próprio dispositivo (interface de endpoint)
        self.volume = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None
        )
        self.volume = cast(self.volume, POINTER(IAudioEndpointVolume))

    def get_volume(self):
        try:
            # Retorna o volume como valor de 0 a 100
            return self.volume.GetMasterVolumeLevelScalar() * 100
        except Exception:
            return 0.0

    def set_volume(self, value):
        try:
            # Garante que o valor está entre 0.0 e 1.0 (0% a 100%)
            vol = max(0.0, min(1.0, value / 100.0))
            self.volume.SetMasterVolumeLevelScalar(vol, None)
        except Exception as e:
            print(f"Erro ao definir volume: {e}")