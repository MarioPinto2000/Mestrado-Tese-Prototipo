import cv2
import pyautogui
import numpy as np
import threading
from gestures.hand_detector import HandDetector
from gestures.hand_analyzer import HandAnalyzer
from gestures.gesture_controller import GestureController
from voice.voice_commands import VoiceController 

# Configurações de performance
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# Variáveis globais para o HUD
status_voz_hud = "Status de voz: A aguardar..."
ultima_detecao = "Voz detectada: ---"

def main():
    global status_voz_hud, ultima_detecao
    
    detector = HandDetector(max_num_hands=2)
    analyzer = HandAnalyzer()
    controller = GestureController()
    voice = VoiceController()
    
    screen_width, screen_height = pyautogui.size()
    frame_margin = 100 
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Processamento de imagem
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (640, 480))
        h_cam, w_cam, _ = frame.shape
        
        _, hands_landmarks, confidences, labels = detector.detect_hands(frame)
        status_text = "Modo: Inativo"
        color = (200, 200, 200)
        
        if hands_landmarks:
            is_active = controller.update_state(labels, hands_landmarks, analyzer)
            
            if is_active:
                if controller.voice_mode_active:
                    if not voice.is_listening:
                        def listen_thread():
                            global status_voz_hud, ultima_detecao
                            status_voz_hud = "Status de voz: A ouvir..."
                            
                            # Chama o script de voz
                            resultado = voice.listen_for_slide()
                            
                            # Tratamento para receber (texto, numero) ou apenas texto
                            if isinstance(resultado, tuple):
                                texto_ouvido = resultado[0]
                            else:
                                texto_ouvido = resultado

                            if texto_ouvido:
                                ultima_detecao = f"Voz detectada: {texto_ouvido}"
                            
                            status_voz_hud = "Status de voz: Pronto"

                        threading.Thread(target=listen_thread, daemon=True).start()
                    
                    status_text = "MODO VOZ ATIVO"
                    color = (0, 255, 255) # Ciano
                else:
                    status_text = controller.get_right_hand_command(labels, hands_landmarks, analyzer)
                    color = (0, 255, 0) # Verde
            
            # Laser (Rato)
            if controller.zoom_mode_active and controller.laser_active:
                for i, label in enumerate(labels):
                    if label == "Right":
                        hand = hands_landmarks[i]
                        x8, y8 = hand[8].x * w_cam, hand[8].y * h_cam
                        mouse_x = np.interp(x8, (frame_margin, w_cam - frame_margin), (0, screen_width))
                        mouse_y = np.interp(y8, (frame_margin, h_cam - frame_margin), (0, screen_height))
                        pyautogui.moveTo(mouse_x, mouse_y)
                        cv2.circle(frame, (int(x8), int(y8)), 8, (0, 0, 255), -1)

            frame = detector.draw_hand_landmarks(frame, hands_landmarks)

        # --- HUD SUPERIOR (Modo à esquerda, Cooldown à direita) ---
        cv2.rectangle(frame, (0, 0), (640, 45), (20, 20, 20), -1)
        # Modo atual
        cv2.putText(frame, status_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # COOLDOWN (Canto superior direito)
        is_ready, time_left = controller.get_cooldown_status()
        cd_text = "PRONTO" if is_ready else f"AGUARDE: {time_left:.1f}s"
        cv2.putText(frame, cd_text, (430, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                    (0, 255, 0) if is_ready else (0, 165, 255), 2)

        # --- HUD INFERIOR (Status de Voz e Última Deteção) ---
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 410), (640, 480), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        cv2.putText(frame, status_voz_hud, (15, 435), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, ultima_detecao, (15, 465), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        cv2.imshow("Controle de Apresentacao v1.0", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()