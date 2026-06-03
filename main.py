import cv2
import pyautogui
import numpy as np
import threading
import time
import subprocess  
import os          
from gestures.hand_detector import HandDetector
from gestures.hand_analyzer import HandAnalyzer
from gestures.gesture_controller import GestureController
from voice.voice_commands import VoiceController 
from audio.audio_utils import AudioController
from metrics_logger import MetricsLogger

# Importações oficiais do ecossistema Windows
import win32com.client
import pythoncom
import win32gui
import win32con

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

status_voz_hud = "Status de voz: A aguardar..."
ultima_detecao = "Voz detectada: ---"

logger = MetricsLogger()

def draw_horizontal_volume_bar(frame, volume):
    h, w, _ = frame.shape
    bar_width = 180   
    bar_height = 15   

    bar_x = (w - bar_width) // 2
    bar_y = h - 35

    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
    fill_width = int((min(volume, 100) / 100) * bar_width)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), (0, 255, 0), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 1)

    cv2.putText(frame, f"{int(volume)}%", (bar_x + bar_width + 5, bar_y + 12), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

def main(cam_index=0, mic_index=None, ppt_path=None, salvar_metricas=True):
    global status_voz_hud, ultima_detecao
    
    # 1. MINIMIZAR A INTERFACE GRÁFICA LOGO NO INÍCIO
    hwnd_interface = win32gui.FindWindow(None, "Controlo Gestual PowerPoint v1.1")
    if hwnd_interface:
        win32gui.ShowWindow(hwnd_interface, win32con.SW_MINIMIZE)
    
    hwnd_ppt_slideshow = None
    
    # 2. SEURANÇA ANTIDUPLICADO: MATAR INSTÂNCIAS ANTIGAS REPETIDAS DO POWERPOINT
    if ppt_path:
        print("A limpar processos antigos do PowerPoint para evitar duplicações...")
        subprocess.run("taskkill /f /im powerpnt.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1) # Aguarda o Windows libertar a memória
    
    # 3. ABRIR APENAS UM POWERPOINT DIRETAMENTE EM FULLSCREEN
    if ppt_path and os.path.exists(ppt_path):
        print(f"A iniciar PowerPoint: {ppt_path}")
        caminho_formatado = os.path.abspath(ppt_path)
        
        try:
            pythoncom.CoInitialize()
            # Cria uma instância limpa e isolada
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            ppt_app.Visible = True 
            
            apresentacao = ppt_app.Presentations.Open(caminho_formatado)
            print("A forçar modo de Apresentação de Diaporamas...")
            apresentacao.SlideShowSettings.Run()
            
            # Pequeno tempo para o PowerPoint criar o ecrã inteiro graficamente
            time.sleep(2)
            
            # Encontra a janela de apresentação do PPT e força-a a vir para a frente de tudo
            hwnd_ppt_slideshow = win32gui.FindWindow("screenClass", None)
            if hwnd_ppt_slideshow:
                win32gui.ShowWindow(hwnd_ppt_slideshow, win32con.SW_SHOWMAXIMIZED)
                win32gui.SetForegroundWindow(hwnd_ppt_slideshow)
            
        except Exception as e:
            print(f"Erro ao abrir via API COM: {e}")
            # Fallback seguro caso o COM falhe gravemente
            os.startfile(caminho_formatado)
            time.sleep(2)
            pyautogui.press('f5')
            time.sleep(1)
            hwnd_ppt_slideshow = win32gui.FindWindow("screenClass", None)
    
    detector = HandDetector(max_num_hands=2)
    analyzer = HandAnalyzer()
    controller = GestureController()
    
    voice = VoiceController(mic_index=mic_index)
    
    screen_width, screen_height = pyautogui.size()
    frame_margin = 60 
    
    # Inicializa o dispositivo de captura da câmara
    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
    audio = AudioController()

    nome_janela = "Controle de Apresentacao v1.0"
    cv2.namedWindow(nome_janela)
    
    # 4. CONFIGURAR A JANELA DA CÂMARA NO TOPO ABSOLUTO (À FRENTE DA APRESENTAÇÃO)
    pos_x = screen_width - 320
    pos_y = 0
    cv2.moveWindow(nome_janela, pos_x, pos_y)
    
    hwnd_camara = win32gui.FindWindow(None, nome_janela)
    if hwnd_camara:
        # HWND_TOPMOST coloca obrigatoriamente a câmara à frente do PowerPoint Fullscreen
        win32gui.SetWindowPos(hwnd_camara, win32con.HWND_TOPMOST, pos_x, pos_y, 320, 240, win32con.SWP_SHOWWINDOW)

    ultimo_comando_registado = None
    
    while True:
        start_frame_time = time.time()
        
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (320, 240))
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
                            status_voz_hud = "Voz: A ouvir..."
                            
                            start_voice_time = time.time()
                            resultado = voice.listen_for_slide()
                            end_voice_time = time.time()
                            voice_latency_ms = (end_voice_time - start_voice_time) * 1000
                            
                            texto_ouvido = resultado[0] if isinstance(resultado, tuple) else resultado
                            
                            if texto_ouvido:
                                texto_valido = str(texto_ouvido).strip().lower()
                                ultima_detecao = f"Ouvido: {texto_valido}"
                                
                                if "slide" in texto_valido or "go to" in texto_valido:
                                    logger.log_voice_attempt(voice_latency_ms, success=True)
                                else:
                                    logger.log_voice_attempt(voice_latency_ms, success=False)
                            else:
                                pass
                                
                            status_voz_hud = "Voz: Pronto"

                        threading.Thread(target=listen_thread, daemon=True).start()
                    
                    status_text = "Escuta Ativa"
                    color_action = (0, 255, 255) 
                else:
                    status_text = controller.get_right_hand_command(labels, hands_landmarks, analyzer)
                    color_action = (0, 255, 0)
                    
                    if status_text and status_text != "...":
                        status_valido = str(status_text).strip().upper().replace("Ç", "C")
                        
                        comandos_de_acao_reais = [
                            "PROXIMO", "ANTERIOR", "AVANCAR", "VOLTAR", "SEGUINTE", 
                            "PLAY", "PAUSE", "PLAY/PAUSE", "MUTE", "RESET", 
                            "CLICK", "ZOOM IN", "ZOOM OUT", "RASTREIO"
                        ]
                        
                        is_comando_real = any(cmd in status_valido for cmd in comandos_de_acao_reais)
                        
                        if is_comando_real:
                            if status_valido != ultimo_comando_registado:
                                logger.log_gesture_attempt()
                                
                                # Garante o foco silencioso na janela do slideshow para enviar as teclas
                                if not hwnd_ppt_slideshow:
                                    hwnd_ppt_slideshow = win32gui.FindWindow("screenClass", None)
                                
                                if hwnd_ppt_slideshow:
                                    win32gui.SetForegroundWindow(hwnd_ppt_slideshow)
                                
                                # Re-afirma que a janela da câmara está por cima imediatamente a seguir ao gesto
                                if hwnd_camara:
                                    win32gui.SetWindowPos(hwnd_camara, win32con.HWND_TOPMOST, pos_x, pos_y, 320, 240, win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
                                
                                ultimo_comando_registado = status_valido
                        else:
                            estados_intermedios = ["DETETADO", "FIXAR", "SEGUIR", "MODO", "ESPERE", "PENDENTE"]
                            if any(est in status_valido for est in estados_intermedios):
                                ultimo_comando_registado = None
                    else:
                        ultimo_comando_registado = None
        else:
            ultimo_comando_registado = None

        if controller.zoom_mode_active and controller.laser_active:
            for i, label in enumerate(labels):
                if label == "Right":
                    hand = hands_landmarks[i]
                    x8, y8 = hand[8].x * w_cam, hand[8].y * h_cam
                    mouse_x = np.interp(x8, (frame_margin, w_cam - frame_margin), (0, screen_width))
                    mouse_y = np.interp(y8, (frame_margin, h_cam - frame_margin), (0, screen_height))
                    pyautogui.moveTo(mouse_x, mouse_y)
                    cv2.circle(frame, (int(x8), int(y8)), 5, (0, 0, 255), -1)

        if hands_landmarks:
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
            color_action = (150, 150, 150)

        is_ready, cd_time_left = controller.get_cooldown_status()
        cd_text = "OK" if is_ready else f"{cd_time_left:.1f}s"
        cd_color = (0, 255, 0) if is_ready else (0, 165, 255)

        cv2.rectangle(frame, (0, 0), (320, 40), (20, 20, 20), -1)
        cv2.putText(frame, f"M: {current_mode_str}", (10, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_mode, 1)
        if current_mode_str != "INATIVO":
            cv2.putText(frame, f"Tempo: {toggle_time_left:.1f}s", (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
        else:
            cv2.putText(frame, f"Acao: {status_text}", (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color_action, 1)
        
        cv2.putText(frame, f"CD: {cd_text}", (230, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, cd_color, 1)

        if controller.voice_mode_active:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 190), (320, 240), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            cv2.putText(frame, status_voz_hud, (10, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
            cv2.putText(frame, ultima_detecao, (10, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)

        if controller.show_mute_overlay:
            cv2.putText(frame, "MUTE", (110, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        end_frame_time = time.time()
        latency_ms = (end_frame_time - start_frame_time) * 1000
        logger.log_gesture_frame(latency_ms)

        cv2.imshow(nome_janela, frame)
        
        # Monitoramento em tempo real: garante que a cada 2 segundos a câmara volta a fixar-se no topo absoluto
        if hwnd_camara and int(time.time()) % 2 == 0:
            win32gui.SetWindowPos(hwnd_camara, win32con.HWND_TOPMOST, pos_x, pos_y, 320, 240, win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)

        if cv2.waitKey(1) & 0xFF == ord('q'): break
        if cv2.getWindowProperty(nome_janela, cv2.WND_PROP_VISIBLE) < 1: break

    cap.release()
    cv2.destroyAllWindows()

    if hwnd_interface:
        win32gui.ShowWindow(hwnd_interface, win32con.SW_RESTORE)

    if salvar_metricas:
        logger.save_report()

if __name__ == "__main__":
    main()