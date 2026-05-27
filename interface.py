import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk  # Necessário para as Comboboxes
import threading
from main import main

# Importar as lógicas de listagem do hardware
from select_camara import listar_camaras
from select_microfone import listar_microfones

class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Controlo Gestual PowerPoint v1.0")

        # Janela ligeiramente maior para acomodar as novas opções confortavelmente
        width, height = 450, 420
        self.center_window(self.root, width, height)
        self.root.configure(bg="#1e1e2e")

        tk.Label(
            root,
            text="MENU PRINCIPAL",
            font=("Segoe UI", 16, "bold"),
            bg="#1e1e2e",
            fg="#89b4fa"
        ).pack(pady=15)

        # --- SELEÇÃO DE CÂMARA ---
        tk.Label(root, text="Selecione a Câmara:", font=("Segoe UI", 10), bg="#1e1e2e", fg="#cdd6f4").pack(pady=2)
        self.combo_camara = ttk.Combobox(root, width=35, state="readonly")
        self.combo_camara.pack(pady=5)

        # --- SELEÇÃO DE MICROFONE ---
        tk.Label(root, text="Selecione o Microfone:", font=("Segoe UI", 10), bg="#1e1e2e", fg="#cdd6f4").pack(pady=2)
        self.combo_microfone = ttk.Combobox(root, width=35, state="readonly")
        self.combo_microfone.pack(pady=5)

        # Popular as Comboboxes com os dispositivos de hardware reais
        self.carregar_dispositivos()

        # --- BOTÕES ---
        self.btn_manual = tk.Button(
            root,
            text="MANUAL DE GESTOS",
            command=self.open_manual,
            width=25,
            height=2,
            bg="#fab387",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2"
        )
        self.btn_manual.pack(pady=10)

        self.btn_start = tk.Button(
            root,
            text="INICIAR SISTEMA",
            command=self.run_main,
            width=25,
            height=2,
            bg="#a6e3a1",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2"
        )
        self.btn_start.pack(pady=10)

    def carregar_dispositivos(self):
        # Configurar listagem de Câmaras
        camaras_disponiveis = listar_camaras()
        if camaras_disponiveis:
            self.combo_camara['values'] = [f"Câmara ID: {idx}" for idx in camaras_disponiveis]
            self.combo_camara.current(0) # Seleciona a primeira por padrão
        else:
            self.combo_camara['values'] = ["Nenhuma câmara detetada"]
            self.combo_camara.current(0)

        # Configurar listagem de Microfones
        mics_disponiveis = listar_microfones()
        if mics_disponiveis:
            # Armazena a lista de tuplos para mapear o índice correto depois
            self.lista_mics_raw = mics_disponiveis
            self.combo_microfone['values'] = [f"[{item[0]}] {item[1]}" for item in mics_disponiveis]
            self.combo_microfone.current(0)
        else:
            self.lista_mics_raw = []
            self.combo_microfone['values'] = ["Nenhum microfone detetado"]
            self.combo_microfone.current(0)

    def center_window(self, win, w, h):
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width // 2) - (w // 2)
        y = (screen_height // 2) - (h // 2)
        win.geometry(f'{w}x{h}+{x}+{y}')

    def open_manual(self):
        manual_win = tk.Toplevel(self.root)
        manual_win.title("Manual de Gestos")
        self.center_window(manual_win, 750, 750)
        manual_win.configure(bg="#1e1e2e")

        txt = scrolledtext.ScrolledText(
            manual_win, bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 11),
            padx=25, pady=25, insertbackground="white", bd=0, wrap=tk.WORD
        )
        txt.pack(fill=tk.BOTH, expand=True)

        txt.tag_configure("titulo", font=("Segoe UI", 18, "bold"), foreground="#89b4fa", justify="center")
        txt.tag_configure("seccao", font=("Segoe UI", 14, "bold"), foreground="#a6e3a1")
        txt.tag_configure("gesto", font=("Segoe UI", 11, "bold"), foreground="#fab387")
        txt.tag_configure("normal", font=("Segoe UI", 11))

        def adicionar_item(nome, desc):
            txt.insert(tk.INSERT, f"{nome}\n", "gesto")
            txt.insert(tk.INSERT, f"{desc}\n\n", "normal")

        txt.insert(tk.INSERT, "MANUAL DE GESTOS\n\n", "titulo")
        txt.insert(tk.INSERT, "INTRODUÇÃO\n\n", "seccao")
        txt.insert(
            tk.INSERT,
            "O sistema funciona através da deteção de gestos com ambas as mãos.\n"
            "A mão esquerda é utilizada para selecionar o modo de funcionamento, "
            "definindo o tipo de comando que o utilizador pretende executar.\n\n"
            "Após a seleção do modo, a mão direita é responsável por realizar o gesto "
            "específico que executa a ação correspondente.\n\n"
            "DICA: Aguarde cerca de 2 segundos entre gestos para evitar múltiplos comandos.\n\n"
            "NOTA: Para fechar o Comando gestual pressione 'q' no teclado\n\n",
            "normal"
        )

        txt.insert(tk.INSERT, "MÃO ESQUERDA → SELEÇÃO DE MODOS\n\n", "seccao")
        adicionar_item("• MODO NAVEGAÇÃO", "Estique apenas o dedo indicador.")
        adicionar_item("• MODO ZOOM / LASER", "Estique o indicador e o dedo médio.")
        adicionar_item("• MODO MULTIMÉDIA", "Estique indicador, médio e anelar.")
        adicionar_item("• MODO VOZ", "Estique o indicador, médio, anelar e mindinho .")

        txt.insert(tk.INSERT, "\nMÃO DIREITA → AÇÕES\n\n", "seccao")
        adicionar_item("• NAVEGAÇÃO", "Swipe em espelho com a mão direita:\n- Da direita para a esquerda → Próximo slide\n- Da esquerda para a direita → Slide Anterior")
        adicionar_item("• FOCUS", "Mão fechada abra a mão → Zoom +\nMão Aberta feche a mão → Zoom -\nGesto OK → Reset do zoom")
        adicionar_item("• MULTIMÉDIA", "Gesto OK → Play / Pause\nIndicador e Médio esticados → Mute/Unmute\nIndicador esticado para cima controla o volume através do deslocamento horizontal.")

        txt.insert(tk.INSERT, "\nVOZ\n\n", "seccao")
        txt.insert(tk.INSERT, "Diga: 'Go to slide [número]' → Navegação para slide especifico\n\n", "normal")
        txt.configure(state=tk.DISABLED)

    def run_main(self):
        # 1. Obter índice da Câmara
        texto_cam = self.combo_camara.get()
        if "Câmara ID:" in texto_cam:
            idx_camara = int(texto_cam.split(":")[-1].strip())
        else:
            idx_camara = 0 # Fallback padrão

        # 2. Obter índice do Microfone
        idx_combo_mic = self.combo_microfone.current()
        if self.lista_mics_raw and idx_combo_mic >= 0:
            idx_microfone = self.lista_mics_raw[idx_combo_mic][0]
        else:
            idx_microfone = None # Deixa o speech_recognition escolher o padrão do SO

        self.btn_start.config(state=tk.DISABLED, text="SISTEMA ATIVO", bg="#45475a")
        
        # Passa as variáveis para a execução paralela
        def thread_wrapper():
            main(cam_index=idx_camara, mic_index=idx_microfone)
            self.root.after(0, self.reset_button)

        threading.Thread(target=thread_wrapper, daemon=True).start()

    def reset_button(self):
        self.btn_start.config(state=tk.NORMAL, text="INICIAR SISTEMA", bg="#a6e3a1")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppUI(root)
    root.mainloop()