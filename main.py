import cv2
from gestures.hand_detector import HandDetector
from gestures.hand_analyzer import HandAnalyzer
from gestures.gesture_controller import GestureController

def main():
    # Inicializa os módulos
    detector = HandDetector(max_num_hands=2)
    analyzer = HandAnalyzer()
    controller = GestureController()
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Erro: Não foi possível abrir a webcam")
        return
    
    print("=== Sistema de Gestos com HUD de Cooldown ===")
    print("Pressione 'p' para ver a análise técnica completa no terminal.")
    print("Pressione 'q' para sair.")
    
    while True:
        ret, frame = cap.read()
        if not ret: 
            break
        
        # Espelhamento para que esquerda/direita sejam naturais
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (640, 480))
        
        # 1. Detecção (Extrai: Frame, Marcos, Confiança, Lados)
        _, hands_landmarks, confidences, labels = detector.detect_hands(frame)
        
        # Variáveis de UI padrão
        status_text = "Modo: Inativo"
        color = (0, 0, 255) # Vermelho (Inativo)
        
        if hands_landmarks:
            # 2. Lógica do Controlador (Mão Esquerda ativa, Mão Direita comanda)
            is_active = controller.update_state(labels, hands_landmarks, analyzer)
            
            if is_active:
                status_text = controller.get_right_hand_command(labels, hands_landmarks, analyzer)
                color = (0, 255, 0) # Verde (Ativo)
            
            # 3. Desenho Visual dos Landmarks
            frame = detector.draw_hand_landmarks(frame, hands_landmarks)
            for i, hand in enumerate(hands_landmarks):
                # Desenha IDs e nomes dos dedos
                frame = analyzer.draw_landmarks_with_info(frame, hand, show_labels=True)
                
                # Texto identificando qual mão é qual sobre o pulso
                lado = labels[i]
                x_p = int(hand[0].x * 640)
                y_p = int(hand[0].y * 480)
                cv2.putText(frame, f"{lado}", (x_p, y_p - 15), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # --- NOVO: CÓDIGO DO HUD DE COOLDOWN (Canto Superior Direito) ---
        is_ready, time_left = controller.get_cooldown_status()
        cd_color = (0, 255, 0) if is_ready else (0, 0, 255)  # Verde se pronto, Vermelho se esperando
        cd_text = "READY" if is_ready else f"WAIT: {time_left:.1f}s"
        
        # Desenha o estado do cooldown no canto superior direito
        cv2.putText(frame, cd_text, (480, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, cd_color, 2)
        # ---------------------------------------------------------------

        # Barra de Status no topo (Modo Atual)
        cv2.rectangle(frame, (0, 0), (450, 40), (0, 0, 0), -1)
        cv2.putText(frame, status_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow("Sistema de Controle Multimodal", frame)
        
        # 4. Gestão de Teclas
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
            
        # DEBUG: Mantém o print detalhado ao pressionar 'p'
        elif key == ord('p') and hands_landmarks:
            print("\n" + "="*50)
            print("DEBUG DE LANDMARKS - TERMINAL")
            print(f"Modo Comando Ativo: {controller.command_mode_active}")
            print(f"Modo Zoom Ativo: {controller.zoom_mode_active}")
            print("="*50)
            for i, hand in enumerate(hands_landmarks):
                print(f"Mão {i+1} [{labels[i]}]:")
                analyzer.print_hand_analysis(hand)
            print("="*50 + "\n")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()