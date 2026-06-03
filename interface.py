import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog
import threading
import os
from main import main
from select_camara import listar_camaras
from select_microfone import listar_microfones

class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Controlo Gestual PowerPoint v1.1")
        self.pptx_path = None 

        width, height = 450, 560 
        self.center_window(self.root, width, height)
        self.root.configure(bg="#1e1e2e")

        tk.Label(root, text="SISTEMA DE APRESENTAÇÃO", font=("Segoe UI", 16, "bold"),
                 bg="#1e1e2e", fg="#89b4fa").pack(pady=15)

        # --- SELEÇÃO DE HARDWARE ---
        tk.Label(root, text="Câmara:", bg="#1e1e2e", fg="#cdd6f4").pack()
        self.combo_camara = ttk.Combobox(root, width=35, state="readonly")
        self.combo_camara.pack(pady=5)

        tk.Label(root, text="Microfone:", bg="#1e1e2e", fg="#cdd6f4").pack()
        self.combo_microfone = ttk.Combobox(root, width=35, state="readonly")
        self.combo_microfone.pack(pady=5)

        # --- SELEÇÃO DE FICHEIRO PPTX ---
        tk.Label(root, text="Apresentação PowerPoint:", bg="#1e1e2e", fg="#cdd6f4").pack(pady=(10,0))
        self.lbl_ficheiro = tk.Label(root, text="Nenhum ficheiro selecionado", 
                                     bg="#1e1e2e", fg="#a6e3a1", font=("Segoe UI", 9, "italic"))
        self.lbl_ficheiro.pack(pady=2)
        
        self.btn_file = tk.Button(root, text="ESCOLHER POWERPOINT", command=self.escolher_ficheiro,
                                  bg="#cba6f7", font=("Segoe UI", 9, "bold"), width=20, relief="flat", cursor="hand2")
        self.btn_file.pack(pady=5)

        self.carregar_dispositivos()

        #Checkbox 
        self.chk_salvar_var = tk.BooleanVar(value=True)
        self.chk_salvar = tk.Checkbutton(
            root, 
            text="Gravar histórico e métricas de desempenho", 
            variable=self.chk_salvar_var,
            bg="#1e1e2e", fg="#cdd6f4", selectcolor="#1e1e2e",
            activebackground="#1e1e2e", activeforeground="#a6e3a1",
            font=("Segoe UI", 10), cursor="hand2"
        )
        self.chk_salvar.pack(pady=10)

        # --- BOTÕES DE EXECUÇÃO ---
        self.btn_manual = tk.Button(root, text="MANUAL DE GESTOS", command=self.open_manual,
                                    width=25, height=2, bg="#fab387", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2")
        self.btn_manual.pack(pady=5)

        self.btn_start = tk.Button(root, text="INICIAR SISTEMA", command=self.run_main,
                                   width=25, height=2, bg="#a6e3a1", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2")
        self.btn_start.pack(pady=10)

    def escolher_ficheiro(self):
        filename = filedialog.askopenfilename(
            title="Selecionar Apresentação",
            filetypes=[("PowerPoint files", "*.pptx *.ppt")]
        )
        if filename:
            self.pptx_path = filename
            self.lbl_ficheiro.config(text=os.path.basename(filename))

    def carregar_dispositivos(self):
        camaras = listar_camaras()
        self.combo_camara['values'] = [f"Câmara ID: {idx}" for idx in camaras] if camaras else ["Nenhuma detetada"]
        self.combo_camara.current(0)

        mics = listar_microfones()
        self.lista_mics_raw = mics
        self.combo_microfone['values'] = [f"[{m[0]}] {m[1]}" for m in mics] if mics else ["Nenhum detetado"]
        self.combo_microfone.current(0)

    def center_window(self, win, w, h):
        x = (win.winfo_screenwidth() // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f'{w}x{h}+{x}+{y}')

    def run_main(self):
        try:
            cam_text = self.combo_camara.get()
            idx_camara = int(cam_text.split(":")[-1].strip()) if "ID:" in cam_text else 0
            
            idx_combo_mic = self.combo_microfone.current()
            idx_microfone = self.lista_mics_raw[idx_combo_mic][0] if self.lista_mics_raw else None
        except:
            idx_camara, idx_microfone = 0, None

        deve_salvar = self.chk_salvar_var.get()

        self.btn_start.config(state=tk.DISABLED, text="SISTEMA ATIVO", bg="#45475a")
        
        def thread_wrapper():
            main(cam_index=idx_camara, mic_index=idx_microfone, ppt_path=self.pptx_path, salvar_metricas=deve_salvar)
            self.root.after(0, self.reset_button)

        threading.Thread(target=thread_wrapper, daemon=True).start()

    def reset_button(self):
        self.btn_start.config(state=tk.NORMAL, text="INICIAR SISTEMA", bg="#a6e3a1")

    # --- MANUAL ---
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
            "normal",
            "NOTA2: Ao criar a sua apresentação PowerPoint tenha em conta que irá aparecer\n\n",
            "uma janela pequena com camara no canto superior direito."
            
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

if __name__ == "__main__":
    root = tk.Tk()
    app = AppUI(root)
    root.mainloop()