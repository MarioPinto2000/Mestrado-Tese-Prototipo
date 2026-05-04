import cv2
import pyautogui
import numpy as np
import threading
from gestures.hand_detector import HandDetector
from gestures.hand_analyzer import HandAnalyzer
from gestures.gesture_controller import GestureController
from voice.voice_commands import VoiceController 

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

def main():
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
                    # Lógica de Threading para não congelar a câmara
                    if not voice.is_listening:
                        threading.Thread(target=voice.listen_for_slide, daemon=True).start()
                    
                    status_text = "A OUVIR VOZ..."
                    color = (0, 255, 255)
                else:
                    status_text = controller.get_right_hand_command(labels, hands_landmarks, analyzer)
                    color = (0, 255, 0)
            
            # Lógica do Rato (Laser)
            if controller.zoom_mode_active and controller.laser_active:
                for i, label in enumerate(labels):
                    if label == "Right":
                        hand = hands_landmarks[i]
                        x8, y8 = hand[8].x * w_cam, hand[8].y * h_cam
                        mouse_x = np.interp(x8, (frame_margin, w_cam - frame_margin), (0, screen_width))
                        mouse_y = np.interp(y8, (frame_margin, h_cam - frame_margin), (0, screen_height))
                        pyautogui.moveTo(mouse_x, mouse_y)
                        cv2.circle(frame, (int(x8), int(y8)), 8, (0, 0, 255), -1)
                        color = (0, 0, 255)

            frame = detector.draw_hand_landmarks(frame, hands_landmarks)

        # HUD
        cv2.rectangle(frame, (0, 0), (640, 45), (0, 0, 0), -1)
        cv2.putText(frame, status_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        is_ready, time_left = controller.get_cooldown_status()
        cd_text = "PRONTO" if is_ready else f"AGUARDE: {time_left:.1f}s"
        cv2.putText(frame, cd_text, (450, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if is_ready else (0, 165, 255), 2)

        cv2.imshow("Controle de Apresentacao v1.0", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()