import cv2
import pyautogui
import numpy as np
from gestures.hand_detector import HandDetector
from gestures.hand_analyzer import HandAnalyzer
from gestures.gesture_controller import GestureController

# Configurações de performance do PyAutoGUI
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

def main():
    detector = HandDetector(max_num_hands=2)
    analyzer = HandAnalyzer()
    controller = GestureController()
    
    # Obter resolução do monitor para o mapeamento do rato
    screen_width, screen_height = pyautogui.size()
    
    # Margem para facilitar o alcance dos cantos do monitor
    frame_margin = 100 

    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (640, 480))
        h_cam, w_cam, _ = frame.shape
        
        # 1. Detecção de mãos
        _, hands_landmarks, confidences, labels = detector.detect_hands(frame)
        
        status_text = "Modo: Inativo"
        color = (200, 200, 200) # Cinza para inativo
        
        if hands_landmarks:
            # 2. Atualizar estado (Navegação ou Zoom)
            is_active = controller.update_state(labels, hands_landmarks, analyzer)
            
            if is_active:
                status_text = controller.get_right_hand_command(labels, hands_landmarks, analyzer)
                color = (0, 255, 0) # Verde quando um modo está ativo
            
            # 3. Lógica do Rato (Apontador) no Modo Zoom
            if controller.zoom_mode_active and controller.laser_active:
                for i, label in enumerate(labels):
                    if label == "Right":
                        hand = hands_landmarks[i]
                        # Posição da ponta do indicador
                        x8, y8 = hand[8].x * w_cam, hand[8].y * h_cam
                        
                        # Mapeamento para o monitor real
                        mouse_x = np.interp(x8, (frame_margin, w_cam - frame_margin), (0, screen_width))
                        mouse_y = np.interp(y8, (frame_margin, h_cam - frame_margin), (0, screen_height))
                        
                        pyautogui.moveTo(mouse_x, mouse_y)
                        
                        # Feedback visual do Laser no frame
                        cv2.circle(frame, (int(x8), int(y8)), 8, (0, 0, 255), -1)
                        color = (0, 0, 255) # Texto em vermelho quando o laser está ON

            # Desenhar as conexões da mão
            frame = detector.draw_hand_landmarks(frame, hands_landmarks)

        # --- HUD: BARRA DE STATUS SUPERIOR ---
        cv2.rectangle(frame, (0, 0), (640, 45), (0, 0, 0), -1)
        cv2.putText(frame, status_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # --- HUD: TEMPORIZADOR DE COOLDOWN (COMO ANTES) ---
        is_ready, time_left = controller.get_cooldown_status()
        cd_color = (0, 255, 0) if is_ready else (0, 165, 255) # Verde ou Laranja
        
        if is_ready:
            cd_text = "SISTEMA PRONTO"
        else:
            cd_text = f"AGUARDE: {time_left:.1f}s"
            
        cv2.putText(frame, cd_text, (430, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cd_color, 2)

        # Exibir a janela
        cv2.imshow("Controle de Apresentacao v2.0", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()