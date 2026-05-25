import pyautogui
import time
from typing import List, Dict

class GestureController:
    def __init__(self):
        # --- VARIÁVEIS PARA TOGGLE  ---
        self.mode_timeout = 15.0  
        self.mode_activation_time = 0.0 
        self.last_mode_change_time = 0.0 
        
        # Variaveis de Estado
        self.command_mode_active = False
        self.zoom_mode_active = False
        self.laser_active = False 
        self.multimedia_active = False
        self.voice_mode_active = False
        
        self.last_command_time = 0
        self.cooldown = 2.0  
        
        self.last_volume_time = 0
        self.volume_cooldown = 0.02  
        
        # --- OTIMIZAÇÃO E SUAVIZAÇÃO DE VOLUME ---
        self.volume_anchor_y = None   
        self.volume_threshold = 0.008  # Limiar ligeiramente ajustado para evitar micro-movimentos fantasmas
        self.volume_pose_counter = 0   # Contador de frames estáveis para filtro debounce
        self.y_history = []            # Histórico de posições para média móvel (anti-treme)
        
        # Ancoras para os movimentos do slide
        self.index_anchor_x = None
        self.pinky_anchor_x = None
        self.swipe_threshold = 0.30
        
        # Memoria para movimento do zoom
        self.prev_right_hand_open = False 
        self.prev_right_hand_closed = False
        
    def get_cooldown_status(self):
        current_time = time.time()
        elapsed = current_time - self.last_command_time
        remaining = max(0, self.cooldown - elapsed)
        return remaining == 0, remaining

    def _can_execute(self) -> bool:
        ready, _ = self.get_cooldown_status()
        if ready:
            self.last_command_time = time.time()
            return True
        return False
    
    def _can_execute_volume(self) -> bool:
        current_time = time.time()
        if (current_time - self.last_volume_time) > self.volume_cooldown:
            self.last_volume_time = current_time
            return True
        return False

    def _set_active_mode(self, mode_name: str):
        self.command_mode_active = (mode_name == 'command')
        self.zoom_mode_active = (mode_name == 'zoom')
        self.multimedia_active = (mode_name == 'multimedia')
        self.voice_mode_active = (mode_name == 'voice')

    def update_state(self, labels: List[str], hands_landmarks: List[List], analyzer) -> bool:
        current_time = time.time()
        
        for i, label in enumerate(labels):
            if label == "Left":
                fingers = analyzer.count_extended_fingers(hands_landmarks[i])
                ind, med, ring = fingers['index'], fingers['middle'], fingers['ring']
                pinky = fingers['pinky']

                modo_detectado = None

                if ind and not med and not ring and not pinky:
                    modo_detectado = 'command'
                elif ind and med and not ring and not pinky:
                    modo_detectado = 'zoom'
                elif ind and med and ring and not pinky:
                    modo_detectado = 'multimedia'
                elif ind and med and ring and pinky:
                    modo_detectado = 'voice'
                
                if modo_detectado:
                    modo_atual_ativo = self.command_mode_active or self.zoom_mode_active or self.multimedia_active or self.voice_mode_active
                    
                    if not modo_atual_ativo:
                        self._set_active_mode(modo_detectado)
                        self.mode_activation_time = current_time
                        self.last_mode_change_time = current_time  
                    else:
                        modo_atual = None
                        if self.command_mode_active: modo_atual = 'command'
                        elif self.zoom_mode_active: modo_atual = 'zoom'
                        elif self.multimedia_active: modo_atual = 'multimedia'
                        elif self.voice_mode_active: modo_atual = 'voice'
                        
                        if modo_detectado != modo_atual:
                            if (current_time - self.last_mode_change_time) > 1.5:
                                self._set_active_mode(modo_detectado)
                                self.mode_activation_time = current_time
                                self.last_mode_change_time = current_time  

        if (current_time - self.mode_activation_time) > self.mode_timeout:
            self._set_active_mode(None)
        
        if not self.command_mode_active:
            self.index_anchor_x = None
            self.pinky_anchor_x = None
        if not self.zoom_mode_active:
            self.laser_active = False
        if not self.multimedia_active:
            self.volume_anchor_y = None
            self.volume_pose_counter = 0
            self.y_history.clear()
                
        return self.command_mode_active or self.zoom_mode_active or self.multimedia_active or self.voice_mode_active
    
    def _execute_multimedia_action(self, sw, sh, center_x, center_y):
        import threading 
        pyautogui.moveTo(center_x - 150, center_y + 150, duration=0.2)
        time.sleep(0.1) 
        pyautogui.moveTo(center_x, center_y, duration=0.2)
        time.sleep(0.1)
        pyautogui.click() 
        time.sleep(0.2)
        pyautogui.moveTo(sw - 5, sh - 5, duration=0.1)

    def get_right_hand_command(self, labels: List[str], hands_landmarks: List[List], analyzer) -> str:
        if not self.command_mode_active and not self.zoom_mode_active and not self.multimedia_active and not self.voice_mode_active:
            return "A espera do modo."

        # Encontra o índice da mão direita de forma robusta, ignorando a sua posição X na imagem
        right_hand_idx = None
        for idx, label in enumerate(labels):
            if label == "Right":
                right_hand_idx = idx
                break

        if right_hand_idx is None:
            return "Mao Direita nao detetada"

        # Extrai os dados da mão direita com garantia de alvo correto
        hand = hands_landmarks[right_hand_idx]
        fingers = analyzer.count_extended_fingers(hand)
        
        dedos_principais = [fingers['index'], fingers['middle'], fingers['ring'], fingers['pinky']]
        total_sem_polegar = sum(dedos_principais)
        
        # --- MODO NAVEGAÇÃO ---
        if self.command_mode_active:
            if total_sem_polegar == 1 and fingers['index']:
                ponta_atual_x = hand[8].x 
                
                if self.index_anchor_x is None: 
                    self.index_anchor_x = ponta_atual_x
                    return "Indicador detetado."
                
                # Deslocamento acumulado em relação à âncora inicial fixa
                deslocamento = ponta_atual_x - self.index_anchor_x
                
                cooldown_pronto, _ = self.get_cooldown_status()
                if not cooldown_pronto:
                    # Atualiza a âncora continuamente durante o cooldown para preparar o próximo Swipe
                    self.index_anchor_x = ponta_atual_x
                    return "Cooldown..."
                
                # Limiar dinâmico para evitar disparos acidentais
                threshold_movimento = 0.05 
                
                if deslocamento < -threshold_movimento:
                    if self._can_execute():
                        pyautogui.press('right')
                        self.index_anchor_x = ponta_atual_x  # Faz reset à âncora após execução bem-sucedida
                        return "RASTREIO: Proximo >>"
                elif deslocamento > threshold_movimento:
                    if self._can_execute():
                        pyautogui.press('left')
                        self.index_anchor_x = ponta_atual_x  # Faz reset à âncora após execução bem-sucedida
                        return "RASTREIO: Anterior <<"
                        
                return "A seguir indicador."
            
            else:
                # Se o utilizador fechou a mão ou abriu mais dedos, liberta a âncora para reiniciar o movimento
                self.index_anchor_x = None
                return "Modo Navegacao Ativo"
        
        # --- MODO ZOOM / POINTER / FOCUS ---
        elif self.zoom_mode_active:
            if fingers['index'] and total_sem_polegar == 1:
                self.laser_active = True
                return "APONTADOR ATIVO"
            else:
                self.laser_active = False

            dist_ok = analyzer.calculate_distance((hand[4].x, hand[4].y), (hand[8].x, hand[8].y))
            if dist_ok < 0.10 and fingers['middle'] and fingers['pinky']:
                if self._can_execute():
                    pyautogui.hotkey('ctrl', 'alt', '0')
                    return "RESET ZOOM"

            abertos_total = sum(fingers.values())
            mao_aberta, mao_fechada = abertos_total >= 4, abertos_total <= 1
            
            if self.prev_right_hand_closed and mao_aberta:
                if self._can_execute():
                    for _ in range(3): pyautogui.hotkey('ctrl', '+')
                    self.prev_right_hand_closed = False 
                    return "Zoom In"
            elif self.prev_right_hand_open and mao_fechada:
                if self._can_execute():
                    for _ in range(3): pyautogui.hotkey('ctrl', '-')
                    self.prev_right_hand_open = False 
                    return "Zoom Out"

            self.prev_right_hand_open = (abertos_total >= 4)
            self.prev_right_hand_closed = (abertos_total <= 1)
            return "Modo Focus"
        
        # --- MODO MULTIMÉDIA ---
        elif self.multimedia_active:
            dist_ok = analyzer.calculate_distance((hand[4].x, hand[4].y), (hand[8].x, hand[8].y))
            
            if dist_ok < 0.05 and fingers['middle'] and fingers['ring'] and fingers['pinky']:
                self.volume_pose_counter = 0  
                if self._can_execute(): 
                    sw, sh = pyautogui.size()
                    center_x, center_y = sw // 2, sh // 2
                    
                    import threading
                    action_thread = threading.Thread(
                        target=self._execute_multimedia_action, 
                        args=(sw, sh, center_x, center_y),
                        daemon=True
                    )
                    action_thread.start()
                    return "PLAY/PAUSE..."

            elif fingers['index'] and fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
                self.volume_pose_counter = 0
                if self._can_execute(): 
                    pyautogui.press('volumemute')
                    self.last_mute_time = time.time()
                    return "AUDIO: MUTE/UNMUTE"

            # --- AJUSTE DE VOLUME ---
            else:
                if hasattr(self, 'last_mute_time') and (time.time() - self.last_mute_time < 2.0):
                    self.volume_pose_counter = 0
                    self.volume_anchor_y = None
                    self.y_history.clear()
                    return "Mute Ativo (Bloqueio UI)"

                ponta_x, ponta_y = hand[8].x, hand[8].y
                base_x, base_y = hand[5].x, hand[5].y
                
                dist_indicador = ((ponta_x - base_x)**2 + (ponta_y - base_y)**2)**0.5
                indicador_esticado = dist_indicador > 0.06
                outros_recolhidos = not fingers['middle'] and not fingers['ring'] and not fingers['pinky']

                if (indicador_esticado and outros_recolhidos) or (self.volume_pose_counter > 0):
                    if indicador_esticado and outros_recolhidos:
                        self.volume_pose_counter = min(10, self.volume_pose_counter + 1)
                    else:
                        self.volume_pose_counter -= 1

                    self.y_history.append(hand[8].y)
                    if len(self.y_history) > 5:
                        self.y_history.pop(0)
                    
                    current_y = sum(self.y_history) / len(self.y_history)

                    if self.volume_pose_counter < 3 and self.volume_anchor_y is None:
                        self.volume_anchor_y = current_y
                        return "A validar gesto de Volume..."
                    
                    if self.volume_anchor_y is None:
                        self.volume_anchor_y = current_y
                        return "Volume Pronto"

                    displacement = self.volume_anchor_y - current_y 

                    if abs(displacement) > self.volume_threshold:
                        if self._can_execute_volume():
                            if displacement > 0:
                                pyautogui.press('volumeup')
                            else:
                                pyautogui.press('volumedown')

                            self.volume_anchor_y = self.volume_anchor_y - (displacement * 0.7)
                            return "A alterar volume"
                    
                    return "Modo Volume"
                
                if self.volume_pose_counter == 0:
                    self.volume_anchor_y = None
                    self.y_history.clear()
                    
                return "Modo Multimedia"
        
        # --- MODO VOZ ---
        elif self.voice_mode_active:
            return "Modo Voz Ativo"

        return "Modo Desconhecido"