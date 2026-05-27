import speech_recognition as sr

def listar_microfones():
    print("A procurar microfones disponíveis...\n")
    nomes = sr.Microphone.list_microphone_names()

    if not nomes:
        print("Nenhum microfone encontrado.")
        return []

    for i, nome in enumerate(nomes):
        print(f"[{i}] {nome}")

    return list(range(len(nomes)))

def escolher_microfone():
    indices = listar_microfones()

    if not indices:
        return None

    print("\nEscolhe o índice do microfone que queres usar:")
    escolha = int(input("Número do microfone: "))

    if escolha not in indices:
        print("Índice inválido.")
        return None

    return escolha

def testar_microfone(device_index):
    r = sr.Recognizer()
    with sr.Microphone(device_index=device_index) as source:
        print(f"\nA ouvir no microfone {device_index}...")
        audio = r.listen(source, timeout=3, phrase_time_limit=3)
        print("Áudio capturado com sucesso!")

def main():
    mic_index = escolher_microfone()
    if mic_index is None:
        return

    testar_microfone(mic_index)

if __name__ == "__main__":
    main()
