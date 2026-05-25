import pyautogui
import time
import threading
from typing import List

class GestureController:
    def __init__(self):
        # --- VARIÁVEIS PARA TOGGLE ---
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

        # --- VOLUME ---
        self.volume_anchor_x = None
        self.volume_threshold = 0.008
        self.volume_pose_counter = 0
        self.x_history = []

        # Ancoras para os movimentos do slide
        self.index_anchor_x = None
        self.pinky_anchor_x = None

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
                if ind and not med and not ring and not pinky: modo_detectado = 'command'
                elif ind and med and not ring and not pinky: modo_detectado = 'zoom'
                elif ind and med and ring and not pinky: modo_detectado = 'multimedia'
                elif ind and med and ring and pinky: modo_detectado = 'voice'

                if modo_detectado:
                    modo_atual_ativo = self.command_mode_active or self.zoom_mode_active or self.multimedia_active or self.voice_mode_active
                    if not modo_atual_ativo:
                        self._set_active_mode(modo_detectado)
                        self.mode_activation_time = current_time
                        self.last_mode_change_time = current_time
                    elif (current_time - self.last_mode_change_time) > 1.5:
                        self._set_active_mode(modo_detectado)
                        self.mode_activation_time = current_time
                        self.last_mode_change_time = current_time

        if (current_time - self.mode_activation_time) > self.mode_timeout:
            self._set_active_mode(None)

        if not self.command_mode_active: self.index_anchor_x = None
        if not self.zoom_mode_active: self.laser_active = False
        if not self.multimedia_active:
            self.volume_anchor_x = None
            self.volume_pose_counter = 0
            self.x_history.clear()

        return self.command_mode_active or self.zoom_mode_active or self.multimedia_active or self.voice_mode_active

    def _execute_multimedia_action(self, sw, sh, center_x, center_y):
        pyautogui.moveTo(center_x - 150, center_y + 150, duration=0.2)
        time.sleep(0.1)
        pyautogui.moveTo(center_x, center_y, duration=0.2)
        time.sleep(0.1)
        pyautogui.click()
        time.sleep(0.2)
        pyautogui.moveTo(sw - 5, sh - 5, duration=0.1)

    def get_right_hand_command(self, labels: List[str], hands_landmarks: List[List], analyzer) -> str:
        if not (self.command_mode_active or self.zoom_mode_active or self.multimedia_active or self.voice_mode_active):
            return "A espera do modo."

        right_hand_idx = next((i for i, label in enumerate(labels) if label == "Right"), None)
        if right_hand_idx is None: return "Mao Direita nao detetada"

        hand = hands_landmarks[right_hand_idx]
        fingers = analyzer.count_extended_fingers(hand)
        total_sem_polegar = sum([fingers['index'], fingers['middle'], fingers['ring'], fingers['pinky']])

        # --- MODO NAVEGAÇÃO ---
        if self.command_mode_active:
            if total_sem_polegar == 1 and fingers['index']:
                ponta_atual_x = hand[8].x
                if self.index_anchor_x is None:
                    self.index_anchor_x = ponta_atual_x
                    return "Indicador detetado."
                
                deslocamento = ponta_atual_x - self.index_anchor_x
                if self.get_cooldown_status()[0]:
                    threshold = 0.05
                    if deslocamento < -threshold:
                        if self._can_execute(): pyautogui.press('right'); self.index_anchor_x = ponta_atual_x; return "RASTREIO: Proximo >>"
                    elif deslocamento > threshold:
                        if self._can_execute(): pyautogui.press('left'); self.index_anchor_x = ponta_atual_x; return "RASTREIO: Anterior <<"
                return "A seguir indicador."
            self.index_anchor_x = None
            return "Modo Navegacao Ativo"

        # --- MODO ZOOM / FOCUS ---
        elif self.zoom_mode_active:
            if fingers['index'] and total_sem_polegar == 1:
                self.laser_active = True
                return "APONTADOR ATIVO"
            self.laser_active = False

            dist_ok = analyzer.calculate_distance((hand[4].x, hand[4].y), (hand[8].x, hand[8].y))
            if dist_ok < 0.10 and fingers['middle'] and fingers['pinky']:
                if self._can_execute(): pyautogui.hotkey('ctrl', 'alt', '0'); return "RESET ZOOM"

            abertos_total = sum(fingers.values())
            if self.prev_right_hand_closed and abertos_total >= 4 and self._can_execute():
                for _ in range(3): pyautogui.hotkey('ctrl', '+')
                return "Zoom In"
            elif self.prev_right_hand_open and abertos_total <= 1 and self._can_execute():
                for _ in range(3): pyautogui.hotkey('ctrl', '-')
                return "Zoom Out"
            
            self.prev_right_hand_open = (abertos_total >= 4)
            self.prev_right_hand_closed = (abertos_total <= 1)
            return "Modo Focus"

       # --- MODO MULTIMÉDIA ---
        elif self.multimedia_active:
            # 1. Bloqueio de 2 segundos para o ajuste de volume pós-Mute
            mute_bloqueado = hasattr(self, 'last_mute_time') and (time.time() - self.last_mute_time < 2.0)
            
            # 2. Gestos de Alta Prioridade (Play/Pause e Mute)
            dist_ok = analyzer.calculate_distance((hand[4].x, hand[4].y), (hand[8].x, hand[8].y))
            
            # Gesto Play/Pause (Prioridade 1)
            if dist_ok < 0.05 and fingers['middle'] and fingers['ring'] and fingers['pinky']:
                self.volume_pose_counter = 0  
                if self._can_execute(): 
                    sw, sh = pyautogui.size()
                    threading.Thread(target=self._execute_multimedia_action, args=(sw, sh, sw//2, sh//2), daemon=True).start()
                    return "PLAY/PAUSE..."
            
            # Gesto Mute (Prioridade 2)
            elif fingers['index'] and fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
                self.volume_pose_counter = 0
                if self._can_execute(): 
                    pyautogui.press('volumemute')
                    self.last_mute_time = time.time()
                    return "AUDIO: MUTE/UNMUTE"

            # 3. Ajuste de Volume (Prioridade 3 - Protegido pelo bloqueio)
            elif not mute_bloqueado:
                # Utilizamos o analyzer para consistência com o resto do código
                indicador_esticado = fingers['index']
                outros_recolhidos = not (fingers['middle'] or fingers['ring'] or fingers['pinky'])

                if (indicador_esticado and outros_recolhidos) or (self.volume_pose_counter > 0):
                    # Filtro de estabilidade (Debounce)
                    self.volume_pose_counter = min(10, self.volume_pose_counter + 1) if indicador_esticado else max(0, self.volume_pose_counter - 1)
                    
                    # Média móvel para suavizar o movimento horizontal
                    self.x_history.append(hand[8].x)
                    if len(self.x_history) > 5: self.x_history.pop(0)
                    current_x = sum(self.x_history) / len(self.x_history)

                    # Ancoragem inicial
                    if self.volume_anchor_x is None: 
                        self.volume_anchor_x = current_x
                        return "A validar volume..."
                    
                    # Ajuste de volume real
                    deslocamento = current_x - self.volume_anchor_x
                    if abs(deslocamento) > self.volume_threshold and self._can_execute_volume():
                        pyautogui.press('volumeup' if deslocamento > 0 else 'volumedown')
                        self.volume_anchor_x = current_x
                        return "A alterar volume"
                    
                    return "Modo Volume"
                
                # Reset se a mão mudar de pose
                self.volume_anchor_x = None
                self.x_history.clear()
                return "Modo Multimedia"
            
            else:
                return "Aguardando (Mute Ativo)..."

        return "Modo Desconhecido"