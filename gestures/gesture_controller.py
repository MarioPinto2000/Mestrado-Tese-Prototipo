import pyautogui
import time
from typing import List, Dict

class GestureController:
    def __init__(self):
        self.command_mode_active = False
        self.zoom_mode_active = False
        self.laser_active = False 
        self.multimedia_active = False
        self.voice_mode_active = False
        
        self.last_command_time = 0
        self.cooldown = 3.0
        
        self.last_volume_time = 0
        self.volume_cooldown = 0.05
        
        #volume 
        self.volume_anchor_y = None   
        self.volume_threshold = 0.001  
        self.volume_cooldown = 0.001   
        self.last_volume_time = 0
        
        # Âncoras para os movimentos do slide
        self.index_anchor_x = None
        self.pinky_anchor_x = None
        self.swipe_threshold = 0.12 
        
        # Memória para movimento do zoom
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

    def update_state(self, labels: List[str], hands_landmarks: List[List], analyzer) -> bool:
        self.command_mode_active = False 
        self.zoom_mode_active = False
        self.voice_mode_active = False
        self.multimedia_active = False
        
        for i, label in enumerate(labels):
            if label == "Left":
                fingers = analyzer.count_extended_fingers(hands_landmarks[i])
                ind, med, ring = fingers['index'], fingers['middle'], fingers['ring']
                pinky = fingers['pinky']

                # 1 dedo: Apenas Indicador
                if ind and not med and not ring and not pinky:
                    self.command_mode_active = True
                # 2 dedos: Indicador e Médio
                elif ind and med and not ring and not pinky:
                    self.zoom_mode_active = True
                elif ind and med and ring and not pinky:
                    self.multimedia_active = True
                # Modo voz indicador e mindinho
                elif ind and pinky and not med and not ring:
                    self.voice_mode_active = True
        
        # Limpeza de memória ao sair dos modos
        if not self.command_mode_active:
            self.index_anchor_x = None
            self.pinky_anchor_x = None
        if not self.zoom_mode_active:
            self.laser_active = False
        if not self.multimedia_active:
            self.volume_anchor_y = None
                
        return self.command_mode_active or self.zoom_mode_active or self.multimedia_active or self.voice_mode_active
    
    def _execute_multimedia_action(self, sw, sh, center_x, center_y):
        """Executa a sequência de movimentos e clique sem bloquear a câmara."""
        # 1. Move para longe para garantir detecção de movimento[cite: 5]
        pyautogui.moveTo(center_x - 150, center_y + 150, duration=0.2)
        time.sleep(0.1) 
        
        # 2. Move para o centro para focar o vídeo[cite: 5]
        pyautogui.moveTo(center_x, center_y, duration=0.2)
        time.sleep(0.1)
        
        # 3. Executa o clique[cite: 5]
        pyautogui.click() 
        
        # 4. LIMPEZA: Move para o canto inferior direito[cite: 5]
        time.sleep(0.2)
        pyautogui.moveTo(sw - 5, sh - 5, duration=0.1)

    def get_right_hand_command(self, labels: List[str], hands_landmarks: List[List], analyzer) -> str:
        if not self.command_mode_active and not self.zoom_mode_active and not self.multimedia_active:
            return "Aguardando Ativador (Mao Esq.)"

        for i, label in enumerate(labels):
            if label == "Right":
                hand = hands_landmarks[i]
                fingers = analyzer.count_extended_fingers(hand)
                
                # Ignorar polegar na contagem principal para evitar conflitos
                dedos_principais = [fingers['index'], fingers['middle'], fingers['ring'], fingers['pinky']]
                total_sem_polegar = sum(dedos_principais)
                
                # --- MODO NAVEGAÇÃO ---
                if self.command_mode_active:
                    if total_sem_polegar == 1:
                        if fingers['index']:
                            self.pinky_anchor_x = None
                            current_x = hand[8].x 
                            if self.index_anchor_x is None: self.index_anchor_x = current_x
                            
                            displacement = current_x - self.index_anchor_x
                            if abs(displacement) > self.swipe_threshold:
                                if self._can_execute():
                                    pyautogui.press('right')
                                    self.index_anchor_x = current_x
                                    return "SWIPE: Próximo >>"
                            return "Modo Slide: Indicador"

                        elif fingers['pinky']:
                            self.index_anchor_x = None
                            current_x = hand[20].x 
                            if self.pinky_anchor_x is None: self.pinky_anchor_x = current_x
                            
                            displacement = current_x - self.pinky_anchor_x
                            if abs(displacement) > self.swipe_threshold:
                                if self._can_execute():
                                    pyautogui.press('left')
                                    self.pinky_anchor_x = current_x
                                    return "SWIPE: Anterior <<"
                            return "Modo Slide: Mindinho"
                    
                    self.index_anchor_x = None
                    self.pinky_anchor_x = None
                    return "Use Indicador ou Mindinho"

                # --- MODO ZOOM / POINTER ---
                elif self.zoom_mode_active:
                    # 1. GESTO LASER (Indicador + Médio)
                    if fingers['index'] and fingers['middle'] and total_sem_polegar == 2:
                        self.laser_active = True
                        return "APONTADOR ATIVO"
                    else:
                        self.laser_active = False

                    # 2. RESET ZOOM (Gesto OK)
                    dist_ok = analyzer.calculate_distance((hand[4].x, hand[4].y), (hand[8].x, hand[8].y))
                    if dist_ok < 0.10 and fingers['middle'] and fingers['pinky']:
                        if self._can_execute():
                            pyautogui.hotkey('ctrl', 'alt', '0')
                            return "RESET ZOOM"

                    # 3. ZOOM IN/OUT (Mão Aberta/Fechada)
                    abertos_total = sum(fingers.values())
                    mão_aberta, mão_fechada = abertos_total >= 4, abertos_total <= 1
                    
                    if self.prev_right_hand_closed and mão_aberta:
                        if self._can_execute():
                            for _ in range(3): pyautogui.hotkey('ctrl', '+')
                            self.prev_right_hand_closed = False 
                            return "Zoom In"
                    elif self.prev_right_hand_open and mão_fechada:
                        if self._can_execute():
                            for _ in range(3): pyautogui.hotkey('ctrl', '-')
                            self.prev_right_hand_open = False 
                            return "Zoom Out"

                    self.prev_right_hand_open = (abertos_total >= 4)
                    self.prev_right_hand_closed = (abertos_total <= 1)
                    return "Modo Zoom"
                
                # --- MODO MULTIMÉDIA ---
                elif self.multimedia_active:
                    dist_ok = analyzer.calculate_distance((hand[4].x, hand[4].y), (hand[8].x, hand[8].y))
                    
                    # 1. GESTO DE PAUSA/PLAY (Gesto OK)
                    if dist_ok < 0.05 and fingers['middle'] and fingers['ring'] and fingers['pinky']:
                        if self._can_execute(): 
                            sw, sh = pyautogui.size()
                            center_x, center_y = sw // 2, sh // 2
                            
                            # DISPARA A AÇÃO EM THREAD SEPARADA:
                            # Isto impede que a câmara congele durante os delays
                            import threading
                            action_thread = threading.Thread(
                                target=self._execute_multimedia_action, 
                                args=(sw, sh, center_x, center_y),
                                daemon=True
                            )
                            action_thread.start()
                            
                            return "A EXECUTAR PLAY/PAUSE..."

                    # 2. GESTO DE MUTE (Indicador, Médio e Anelar levantados)
                    elif fingers['index'] and fingers['middle'] and fingers['ring'] and not fingers['pinky']:
                        if self._can_execute(): 
                            pyautogui.press('volumemute')
                            return "AUDIO: MUTE/UNMUTE"

                    # 3. GESTO DE VOLUME PROGRESSIVO (Apenas indicador levantado)[cite: 3]
                    elif fingers['index'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
                        current_y = hand[8].y 
                        
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
                                
                                self.volume_anchor_y = current_y
                                return "Ajustando Volume"
                        
                        return "Modo Volume"
                    
                    self.volume_anchor_y = None
                    return "Modo Multimédia"
    
        return "Mão Direita não detectada"