import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class LoginFormFrame(tk.Frame):
    """Formulário de login"""

    def __init__(self, parent, callbacks, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.senha_var = tk.StringVar()
        self.rgu_var = tk.StringVar()
        rgu_label = ttk.Label(self, text="RGU: ")
        rgu_label.grid(row=0, column=0, sticky=(tk.E))
        senha_label = ttk.Label(self, text="Senha: ")
        senha_label.grid(row=1, column=0, sticky=(tk.E))

        comando_validar_rgu = (self.register(self._validar_digito), '%P')
        rgu_entry = ttk.Entry(self, textvariable=self.rgu_var)
        rgu_entry.grid(row=0, column=1, pady=5, padx=5)
        rgu_entry.config(validate='key', validatecommand=comando_validar_rgu)
        rgu_entry.focus_set()

        self.senha_entry = ttk.Entry(self, show='*',
                                     textvariable=self.senha_var)
        self.senha_entry.grid(row=1, column=1, pady=5, padx=5)

        self.senha_entry.bind('<Return>', callbacks['login'])

        self.lembrar = tk.IntVar()
        self.chkbox_lembrar = ttk.Checkbutton(self, text='Lembrar de mim',
                                              variable=self.lembrar)
        self.chkbox_lembrar.grid(row=2, column=0, pady=5, columnspan=2)

        self.enter_button = ttk.Button(self, command=callbacks['login'], text="Entrar")
        self.enter_button.grid(row=3, column=0, pady=5, columnspan=2)

        rgu_entry.bind('<Return>', lambda e: self.senha_entry.focus_set())

    def _validar_digito(self, proposed: str) -> bool:
        return proposed.isdigit()


class ConsultaFrame(tk.Frame):
    """Frame que mostra o resultado da consutla"""

    def __init__(self, parent, callbacks: dict, dados_salvos=False, *args, **kwargs):
        self.dados_salvos = dados_salvos
        self.parent = parent
        super().__init__(parent, *args, **kwargs)
        self.tree = ttk.Treeview(self, columns=['data', 'info'], height=5)
        self.tree.heading('#0', text='Título')
        self.tree.heading('data', text='Data de entrega prevista')
        self.tree.heading('info', text='Informação')
        self.btn_esquecer = ttk.Button(self, text="Esquecer meu login",
                                       command=callbacks['esquecer_login'])

    def show_deletado_sucesso(self):
        self.btn_esquecer.grid_forget()
        label = ttk.Label(text='Dados de login apagados com sucesso')
        label.grid()

    def show(self):
        self.tree.grid()
        if self.dados_salvos:
            self.btn_esquecer.grid(row=1, column=0, sticky=tk.E)
        self.tkraise()

    def inserir_info(self, emprestimo, info):
        self.tree.insert(
            '',
            'end',
            text=emprestimo['titulo'],
            values=(emprestimo['data'].strftime("%d/%m/%Y"), info)
        )
