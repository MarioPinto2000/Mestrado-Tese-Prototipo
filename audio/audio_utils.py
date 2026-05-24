import platform


def get_volume_windows():
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        # usa o endpoint direto da API de áudio ativa
        enumerator = AudioUtilities.GetDeviceEnumerator()
        device = enumerator.GetDefaultAudioEndpoint(0, 1)

        interface = device.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )

        volume = cast(interface, POINTER(IAudioEndpointVolume))

        return round(volume.GetMasterVolumeLevelScalar() * 100, 2)

    except Exception as e:
        return f"Erro Windows: {e}"


if __name__ == "__main__":
    print(f"🔊 Volume atual: {get_volume_windows()}%")