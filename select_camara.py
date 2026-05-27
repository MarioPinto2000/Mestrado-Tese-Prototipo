import cv2

def listar_camaras():
    print("A procurar câmaras disponíveis...\n")
    indices = []

    # Testar apenas 0, 1 e 2 (normalmente suficiente)
    for i in range(3):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"[{i}] Câmara encontrada")
            indices.append(i)
        cap.release()

    return indices

def escolher_camera():
    indices = listar_camaras()

    if not indices:
        print("Nenhuma câmara encontrada.")
        return None

    print("\nEscolhe o índice da câmara que queres usar:")
    for i in indices:
        print(f" - {i}")

    escolha = int(input("\nNúmero da câmara: "))
    if escolha not in indices:
        print("Índice inválido.")
        return None

    return escolha

def main():
    cam_index = escolher_camera()
    if cam_index is None:
        return

    print(f"\nA abrir a câmara {cam_index}...")
    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao ler frame.")
            break

        cv2.imshow("Câmara selecionada", frame)

        if cv2.waitKey(1) == 27:  # ESC para sair
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
