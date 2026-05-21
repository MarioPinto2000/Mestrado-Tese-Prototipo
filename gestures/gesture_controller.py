import pyautogui
import time
from typing import List, Dict

class GestureController:
    def __init__(self):
        # --- NOVAS VARIÁVEIS PARA O TOGGLE (TEMPORIZADOR) ---
        self.mode_timeout = 15.0  # Tempo em segundos que o modo fica ativo
        self.mode_activation_time = 0.0 # Regista quando o modo foi ativado
        
        # Variáveis de Estado
        self.command_mode_active = False
        self.zoom_mode_active = False
        self.laser_active = False 
        self.multimedia_active = False
        self.voice_mode_active = False
        
        self.last_command_time = 0
        self.cooldown = 1.5
        
        self.last_volume_time = 0
        self.volume_cooldown = 0.05
        
        # volume 
        self.volume_anchor_y = None   
        self.volume_threshold = 0.001  
        
        # Âncoras para os movimentos do slide
        self.index_anchor_x = None
        self.pinky_anchor_x = None
        self.swipe_threshold = 0.20
        
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

    def _set_active_mode(self, mode_name: str):
        """Função auxiliar para ativar apenas um modo e desativar os restantes."""
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

                # 1 dedo: Apenas Indicador (Navegação)
                if ind and not med and not ring and not pinky:
                    modo_detectado = 'command'
                # 2 dedos: Indicador e Médio (Zoom/Laser)
                elif ind and med and not ring and not pinky:
                    modo_detectado = 'zoom'
                # 3 dedos: Multimédia
                elif ind and med and ring and not pinky:
                    modo_detectado = 'multimedia'
                # Modo voz: indicador e mindinho
                elif ind and pinky and not med and not ring:
                    modo_detectado = 'voice'
                
                # SE UM GESTO VÁLIDO FOI DETECTADO:
                if modo_detectado:
                    # 1. Verifica se já existe algum modo ativo.
                    # Se NÃO houver nenhum modo ativo (está tudo desligado), entra logo no modo.
                    modo_atual_ativo = self.command_mode_active or self.zoom_mode_active or self.multimedia_active or self.voice_mode_active
                    
                    if not modo_atual_ativo:
                        self._set_active_mode(modo_detectado)
                        self.mode_activation_time = current_time
                        self.last_command_time = current_time # Inicia o cooldown ao ligar pela primeira vez
                    
                    # 2. Se já houver um modo ativo e estás a tentar MUDAR para outro:
                    # Só permite se o cooldown global de 1.5s já tiver passado
                    else:
                        # Verifica se o modo detectado é diferente do que já está a rodar
                        modo_atual = None
                        if self.command_mode_active: modo_atual = 'command'
                        elif self.zoom_mode_active: modo_atual = 'zoom'
                        elif self.multimedia_active: modo_atual = 'multimedia'
                        elif self.voice_mode_active: modo_atual = 'voice'
                        
                        if modo_detectado != modo_atual:
                            # Se o cooldown permitir, faz a troca e reinicia o relógio
                            if self._can_execute():
                                self._set_active_mode(modo_detectado)
                                self.mode_activation_time = current_time

        # --- VERIFICAÇÃO DO TEMPORIZADOR ---
        # Se passaram 15 segundos desde o último gesto da mão esquerda, desativa todos os modos
        if (current_time - self.mode_activation_time) > self.mode_timeout:
            self._set_active_mode(None)
        
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
        import threading # Garantir que está importado para a thread multimédia
        
        pyautogui.moveTo(center_x - 150, center_y + 150, duration=0.2)
        time.sleep(0.1) 
        pyautogui.moveTo(center_x, center_y, duration=0.2)
        time.sleep(0.1)
        pyautogui.click() 
        time.sleep(0.2)
        pyautogui.moveTo(sw - 5, sh - 5, duration=0.1)

    def get_right_hand_command(self, labels: List[str], hands_landmarks: List[List], analyzer) -> str:
        # Verifica se há algum modo ativo no momento (controlado agora pelo temporizador)
        if not self.command_mode_active and not self.zoom_mode_active and not self.multimedia_active and not self.voice_mode_active:
            return "Aguardando Ativador (Mao Esq.)"

        for i, label in enumerate(labels):
            if label == "Right":
                hand = hands_landmarks[i]
                fingers = analyzer.count_extended_fingers(hand)
                
                dedos_principais = [fingers['index'], fingers['middle'], fingers['ring'], fingers['pinky']]
                total_sem_polegar = sum(dedos_principais)
                
              # --- MODO NAVEGAÇÃO ---
                if self.command_mode_active:
                    if total_sem_polegar == 1:
                        if fingers['index']:
                            
                            # Posição X atual da ponta do indicador
                            ponta_atual_x = hand[8].x 
                            
                            # 1. Se for o primeiro frame com o dedo levantado, inicializa a âncora e sai
                            if self.index_anchor_x is None: 
                                self.index_anchor_x = ponta_atual_x
                                return "Modo Rastreio: Dedo detetado"
                            
                            # 2. Calcula o deslocamento (Velocidade/Direção do movimento)
                            # Frame Atual - Frame Anterior
                            deslocamento = ponta_atual_x - self.index_anchor_x
                            
                            # Atualiza IMEDIATAMENTE a âncora para o próximo frame seguir o dedo (Follow)
                            self.index_anchor_x = ponta_atual_x
                            
                            # 3. VERIFICAÇÃO DO COOLDOWN GLOBAL
                            # Se o teu cooldown de 1.5s ainda estiver a correr, ignoramos o movimento
                            cooldown_pronto, _ = self.get_cooldown_status()
                            if not cooldown_pronto:
                                return "Modo Rastreio: Aguardando Cooldown"
                            
                            # 4. VALIDAÇÃO DO MOVIMENTO (Usa o teu self.swipe_threshold ajustado para sensibilidade)
                            # Como o cálculo é feito frame a frame, o threshold deve ser pequeno (ex: 0.03 a 0.05)
                            # para detetar um movimento rápido de arrasto.
                            threshold_movimento = 0.04 
                            
                            # MOVER PARA A ESQUERDA (Deslocamento negativo: o X diminui) -> Próximo Slide
                            if deslocamento < -threshold_movimento:
                                if self._can_execute():
                                    pyautogui.press('right')
                                    return "RASTREIO: Próximo >>"
                            
                            # MOVER PARA A DIREITA (Deslocamento positivo: o X aumenta) -> Slide Anterior
                            elif deslocamento > threshold_movimento:
                                if self._can_execute():
                                    pyautogui.press('left')
                                    return "RASTREIO: Anterior <<"
                                    
                            return "A seguir a ponta do dedo..."
                    
                    # Se fechar a mão, limpa o rastreio
                    self.index_anchor_x = None
                    return "Use o Indicador para Navegar"
                
                
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

                    # 3. GESTO DE VOLUME PROGRESSIVO (Apenas indicador levantado)
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