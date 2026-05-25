import tkinter as tk
from tkinter import scrolledtext
import threading
from main import main

class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Controlo Gestual PowerPoint v1.0")

        width, height = 400, 250
        self.center_window(self.root, width, height)
        
        self.root.configure(bg="#1e1e2e")

        tk.Label(
            root,
            text="MENU PRINCIPAL",
            font=("Segoe UI", 16, "bold"),
            bg="#1e1e2e",
            fg="#89b4fa"
        ).pack(pady=20)

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

    def center_window(self, win, w, h):
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        
        x = (screen_width // 2) - (w // 2)
        y = (screen_height // 2) - (h // 2)
        
        win.geometry(f'{w}x{h}+{x}+{y}')

    def open_manual(self):
        manual_win = tk.Toplevel(self.root)
        manual_win.title("Manual de Gestos")
        
        # Centrar a janela do manual
        self.center_window(manual_win, 750, 750)
        
        manual_win.configure(bg="#1e1e2e")

        txt = scrolledtext.ScrolledText(
            manual_win,
            bg="#1e1e2e",
            fg="#cdd6f4",
            font=("Segoe UI", 11),
            padx=25,
            pady=25,
            insertbackground="white",
            bd=0,
            wrap=tk.WORD
        )
        txt.pack(fill=tk.BOTH, expand=True)

        # Estilos
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
            "Os comandos devem ser realizados com as duas mãos em simultâneo, "
            "garantindo assim uma deteção correta e evitando ativações indesejadas.\n\n"
            "DICA: Aguarde cerca de 3 segundos entre gestos para evitar múltiplos comandos.\n\n"
            "NOTA: Para fechar o Comando gestual pressione 'q' no teclado\n\n",
            "normal"
        )

        txt.insert(tk.INSERT, "MÃO ESQUERDA → SELEÇÃO DE MODOS\n\n", "seccao")
        adicionar_item("• MODO NAVEGAÇÃO", "Estique apenas o dedo indicador.")
        adicionar_item("• MODO ZOOM / LASER", "Estique o indicador e o dedo médio.")
        adicionar_item("• MODO MULTIMÉDIA", "Estique indicador, médio e anelar.")
        adicionar_item("• MODO VOZ", "Estique o indicador, médio, anelar e mindinho .")

        txt.insert(tk.INSERT, "\nMÃO DIREITA → AÇÕES\n\n", "seccao")
        adicionar_item("• NAVEGAÇÃO", "Swipe semelhante ao movimento de virar a pagina de um livro com o dedo indicador:\n- Da direita para a esquerda → Próximo slide\n- Da esquerda para a direita → Slide Anterior")
        adicionar_item("• FOCUS", "Mão fechada abra a mão → Zoom +\nMão Aberta feche a mão → Zoom -\nGesto OK (ponta do indicador a tocar na ponta do polegar e dedos restantes esticados) → Reset do zoom")
        adicionar_item("• MULTIMÉDIA", "Gesto OK (ponta do indicador a tocar na ponta do polegar e dedos restantes esticados) → Play / Pause\nIndicador e Médio esticados → Mute/Unmute\nIndicador esticado e a apontar para cima o sistema segue o movimento da mão.O movimento da mão para cima aumenta o volume e para baixo diminui")

        txt.insert(tk.INSERT, "\nVOZ\n\n", "seccao")
        txt.insert(tk.INSERT, "Diga: 'Go to slide [número]' → Navegação para slide especifico\n\n", "normal")

        txt.configure(state=tk.DISABLED)

    def run_main(self):
        self.btn_start.config(state=tk.DISABLED, text="SISTEMA ATIVO", bg="#45475a")
        
        def thread_wrapper():
            main()
            self.root.after(0, self.reset_button)

        threading.Thread(target=thread_wrapper, daemon=True).start()

    def reset_button(self):
        self.btn_start.config(state=tk.NORMAL, text="INICIAR SISTEMA", bg="#a6e3a1")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppUI(root)
    root.mainloop()