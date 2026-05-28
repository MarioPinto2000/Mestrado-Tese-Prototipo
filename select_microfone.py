import speech_recognition as sr

def listar_microfones():
    nomes = sr.Microphone.list_microphone_names()
    if not nomes:
        return []

    return [(i, nome) for i, nome in enumerate(nomes)]

def testar_microfone(device_index):
    r = sr.Recognizer()
    with sr.Microphone(device_index=device_index) as source:
        print(f"\nA ouvir no microfone {device_index}...")
        audio = r.listen(source, timeout=3, phrase_time_limit=3)
        print("Áudio capturado com sucesso!")