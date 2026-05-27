import cv2
import pyautogui
import numpy as np
import threading
import time
from gestures.hand_detector import HandDetector
from gestures.hand_analyzer import HandAnalyzer
from gestures.gesture_controller import GestureController
from voice.voice_commands import VoiceController 
from audio.audio_utils import AudioController

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

status_voz_hud = "Status de voz: A aguardar..."
ultima_detecao = "Voz detectada: ---"

def draw_horizontal_volume_bar(frame, volume):
    h, w, _ = frame.shape
    bar_width = 300   
    bar_height = 25   

    bar_x = (w - bar_width) // 2
    bar_y = h - 50

    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)

    fill_width = int((min(volume, 100) / 100) * bar_width)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), (0, 255, 0), -1)

    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 1)

    cv2.putText(frame, f"Volume: {int(volume)}%", (bar_x + bar_width + 10, bar_y + 18), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

def main():
    global status_voz_hud, ultima_detecao
    
    detector = HandDetector(max_num_hands=2)
    analyzer = HandAnalyzer()
    controller = GestureController()
    voice = VoiceController()
    
    screen_width, screen_height = pyautogui.size()
    frame_margin = 100 
    cap = cv2.VideoCapture(0)

    audio = AudioController()
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (640, 480))
        h_cam, w_cam, _ = frame.shape
        
        current_time = time.time()
        _, hands_landmarks, confidences, labels = detector.detect_hands(frame)
        
        if (current_time - controller.mode_activation_time) > controller.mode_timeout:
            controller._set_active_mode(None)

        status_text = "..."
        color_action = (150, 150, 150) 
        
        if hands_landmarks:
            is_active = controller.update_state(labels, hands_landmarks, analyzer)
            
            if is_active:
                if controller.voice_mode_active:
                    if not voice.is_listening:
                        def listen_thread():
                            global status_voz_hud, ultima_detecao
                            status_voz_hud = "Status de voz: A ouvir..."
                            resultado = voice.listen_for_slide()
                            texto_ouvido = resultado[0] if isinstance(resultado, tuple) else resultado
                            if texto_ouvido:
                                ultima_detecao = f"Voz detectada: {texto_ouvido}"
                            status_voz_hud = "Status de voz: Pronto"

                        threading.Thread(target=listen_thread, daemon=True).start()
                    
                    status_text = "Comando de voz em escuta"
                    color_action = (0, 255, 255) 
                else:
                    status_text = controller.get_right_hand_command(labels, hands_landmarks, analyzer)
                    color_action = (0, 255, 0)
            
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

        current_mode_str = "INATIVO"
        color_mode = (150, 150, 150) 
        
        if controller.command_mode_active:
            current_mode_str = "NAVEGACAO"
            color_mode = (255, 150, 50)  
        elif controller.zoom_mode_active:
            current_mode_str = "ZOOM / LASER"
            color_mode = (50, 255, 50)   
        elif controller.multimedia_active:
            current_mode_str = "MULTIMEDIA"
            color_mode = (255, 50, 255)
            
            if controller.show_volume_bar:
                vol = audio.get_volume()
                if isinstance(vol, (int, float)): 
                    draw_horizontal_volume_bar(frame, vol)  
        elif controller.voice_mode_active:
            current_mode_str = "VOZ"
            color_mode = (0, 255, 255)   
            
        toggle_time_left = 0.0
        if current_mode_str != "INATIVO":
            toggle_time_left = max(0, controller.mode_timeout - (current_time - controller.mode_activation_time))
        else:
            status_text = "..."
            color_action = (150, 150, 150)

        is_ready, cd_time_left = controller.get_cooldown_status()
        cd_text = "PRONTO" if is_ready else f"ESPERE: {cd_time_left:.1f}s"
        cd_color = (0, 255, 0) if is_ready else (0, 165, 255)

        # DESENHO DO HUD SUPERIOR
        cv2.rectangle(frame, (0, 0), (640, 60), (20, 20, 20), -1)
        cv2.putText(frame, f"Modo: {current_mode_str}", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_mode, 2)
        if current_mode_str != "INATIVO":
            cv2.putText(frame, f"Tempo Restante: {toggle_time_left:.1f}s", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            cv2.putText(frame, "Faca um gesto com a mao esq.", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        cv2.putText(frame, f"Cooldown: {cd_text}", (400, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cd_color, 2)
        cv2.putText(frame, status_text, (400, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_action, 1)

        if controller.voice_mode_active:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 410), (640, 480), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            cv2.putText(frame, status_voz_hud, (15, 435), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, ultima_detecao, (15, 465), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        if controller.show_mute_overlay:
            cv2.putText(frame, "MUTE", (240, 260), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 255, 0), 4)
        
        cv2.imshow("Controle de Apresentacao v1.0", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        if cv2.getWindowProperty("Controle de Apresentacao v1.0", cv2.WND_PROP_VISIBLE) < 1: break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()