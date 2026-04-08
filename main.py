import cv2
from gestures.hand_detector import HandDetector
from gestures.hand_analyzer import HandAnalyzer

def main():
    detector = HandDetector(max_num_hands=2)
    analyzer = HandAnalyzer()
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Erro: Não foi possível abrir a webcam")
        return
    
    print("Sistema Iniciado.")
    print("Pressione 'p' para imprimir os dados da mão no terminal.")
    print("Pressione 'q' para sair.")
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.resize(frame, (640, 480))
        
        # 1. Detecção
        _, hands_landmarks, confidences = detector.detect_hands(frame)
        
        # 2. Desenho (Esqueleto e IDs)
        if hands_landmarks:
            frame = detector.draw_hand_landmarks(frame, hands_landmarks)
            for hand in hands_landmarks:
                frame = analyzer.draw_landmarks_with_info(frame, hand, show_labels=True)
        
        cv2.imshow("Sistema Multimodal", frame)
        
        # 3. Captura de teclas
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        
        # Se pressionar 'p' e houver uma mão na tela
        elif key == ord('p') and hands_landmarks:
            print("\n--- ANÁLISE DE DADOS (Hand Analyzer) ---")
            for i, hand in enumerate(hands_landmarks):
                # Conta os dedos usando a lógica do analyzer
                dedos = analyzer.count_extended_fingers(hand)
                total = sum(dedos.values())
                print(f"Mão {i+1}: {total} dedos abertos {dedos}")
                
                # Exemplo de distância (entre polegar e indicador)
                dist = analyzer.calculate_distance(
                    (hand[4].x, hand[4].y), 
                    (hand[8].x, hand[8].y)
                )
                print(f"Distância Pinça (Polegar-Indicador): {dist:.4f}")
            print("---------------------------------------")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()