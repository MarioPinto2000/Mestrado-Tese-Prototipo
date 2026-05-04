import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
from main import main 

class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Controlo PowerPoint Gestual v1.0 - Sistema Multimodal")
        self.root.geometry("600x500")
        self.root.configure(bg="#1e1e2e")

        # Título Principal
        self.title_label = tk.Label(
            root, 
            text="CONTROLO DE APRESENTAÇÃO AI", 
            font=("Segoe UI", 18, "bold"),
            bg="#1e1e2e",
            fg="#89b4fa"
        )
        self.title_label.pack(pady=20)

        # Frame para os Botões
        button_frame = tk.Frame(root, bg="#1e1e2e")
        button_frame.pack(pady=10)

        self.btn_start = tk.Button(
            button_frame, 
            text="▶ INICIAR SISTEMA", 
            command=self.run_main,
            width=18,
            height=2,
            bg="#a6e3a1",
            fg="#11111b",
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        self.btn_start.pack(side=tk.LEFT, padx=10)

        self.btn_exit = tk.Button(
            button_frame, 
            text="✕ SAIR", 
            command=root.quit,
            width=10,
            height=2,
            bg="#f38ba8",
            fg="#11111b",
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        self.btn_exit.pack(side=tk.LEFT, padx=10)

        # Área de Instruções (ScrolledText para melhor organização)
        self.instr_area = scrolledtext.ScrolledText(
            root, 
            width=70, 
            height=15, 
            font=("Consolas", 10),
            bg="#313244",
            fg="#cdd6f4",
            padx=10,
            pady=10,
            relief="flat"
        )
        self.instr_area.pack(pady=20, padx=20)
        self.insert_instructions()
        self.instr_area.configure(state=tk.DISABLED) # Apenas leitura

    def insert_instructions(self):
        instr_text = """
============================================================
        MANUAL DE GESTOS E COMANDOS
============================================================

1. MÃO ESQUERDA: SELEÇÃO DE MODOS (Ativador)
------------------------------------------------------------
• INDICADOR           -> Modo Navegação (Slides)
• INDICADOR + MÉDIO   -> Modo Zoom / Laser
• IND + MÉD + ANELAR  -> Modo Multimédia
• IND + MINDINHO      -> Modo Voz (Gesto Rock)

2. MÃO DIREITA: AÇÕES (Comandos)
------------------------------------------------------------
[MODO NAVEGAÇÃO]
• SWIPE INDICADOR (D) -> Próximo Slide
• SWIPE MINDINHO (E)  -> Slide Anterior

[MODO ZOOM / LASER]
• INDICADOR + MÉDIO   -> Mover Apontador Laser
• ABRIR MÃO           -> Zoom In (+)
• FECHAR MÃO          -> Zoom Out (-)
• GESTO OK            -> Reset Zoom (100%)

[MODO MULTIMÉDIA]
• GESTO OK            -> Play / Pausa (Clique no Centro)
• IND + MÉD + ANELAR  -> Mute / Unmute Áudio
• APENAS INDICADOR    -> Volume (Mover p/ Cima ou Baixo)

[MODO VOZ]
• Diga "Go to Slide [número]"    -> Salta para o slide específico
------------------------------------------------------------
Dica: Aguarde o cooldown de 3s entre cliques.
"""
        self.instr_area.insert(tk.INSERT, instr_text)

    def run_main(self):
        """Executa a lógica principal em Thread para não travar a UI[cite: 1]"""
        self.btn_start.config(state=tk.DISABLED, text="SISTEMA ATIVO")
        thread = threading.Thread(target=self.start_backend, daemon=True)
        thread.start()

    def start_backend(self):
        try:
            main() 
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro ao iniciar backend: {e}")
        finally:
            self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL, text="▶ INICIAR SISTEMA"))

if __name__ == "__main__":
    root = tk.Tk()
    app = AppUI(root)
    root.mainloop()