import tkinter as tk
from tkinter import messagebox
import requests
from . import views as v
from . import models as m


class Application(tk.Tk):

    def __init__(self, *args, **kwargs):
        """Inicializa a aplicação"""
        super().__init__(*args, **kwargs)
        self.title("Autore9")
        self.geometry('250x130')
        self.resizable(height=False, width=False)

        self.persistencia_dados = m.PersistenciaDadosLogin()
        dados_salvos = self.persistencia_dados.existem_dados_salvos()
        self.callbakcs_consulta_frame = {
            'esquecer_login': self.esquecer_login
        }

        self.callbacks_login_form = {
            'login': self.login
        }

        self.consulta = v.ConsultaFrame(self, self.callbakcs_consulta_frame,
                                        dados_salvos)
        self.consulta.grid(row=0, column=0)
        self.login_form = v.LoginFormFrame(self, self.callbacks_login_form)
        self.login_form.grid(row=0, column=0)

        self.columnconfigure(0, weight=1)
        if dados_salvos:
            self.lembrar_login()

    def salvar_login(self):
        """Salva os dados do formulário para arquivo"""
        rgu = self.login_form.rgu_var.get()
        senha = self.login_form.senha_var.get()
        try:
            self.persistencia_dados.save_data(rgu, senha)
        except PermissionError:
            messagebox.showwarning(
                "Autore9: ERRO DE PERMISSÃO",
                message="Erro de permissão ao salvar dados")

    def lembrar_login(self):
        """Carrega os dados salvos do usuário e faz a consulta."""
        try:
            rgu, senha = self.persistencia_dados.load_data()
            self.login_form.rgu_var.set(rgu)
            self.login_form.senha_var.set(senha)
            self.login()
        except PermissionError:
            messagebox.showwarning(
                "Autore9: ERRO DE PERMISSÃO",
                message="Sem permissão para acessar dados salvos")

    def login(self, event=None):
        """Realiza a consulta"""
        rgu = self.login_form.rgu_var.get()
        senha = self.login_form.senha_var.get()
        erro = []
        try:
            resultado_consulta = m.Biblioteca.consultar_emprestimo(rgu, senha)
        except requests.ConnectionError:
            erro = ['Erro de conexão']
        except m.ErroConsulta as e:
            erro = [e]

        if erro:
            messagebox.showerror("Autore9: ERRO NA CONSULTA", message=erro[0])
        else:
            self.geometry('')
            self.login_form.grid_forget()
            parser = m.ParserEmprestimos()
            parser.feed(resultado_consulta)
            emprestimos = list(parser)
            self.renovar_necessarios_e_exibir(emprestimos)
            if self.login_form.lembrar.get() == 1:
                self.salvar_login()
    
    def renovar_necessarios_e_exibir(self, emprestimos: list):
        """
        Renova os livros necessários e preenche a tabela.
        
        Arguments:
            emprestimos {list} -- Lista de Emprestimos
        """

        self.consulta.show()
        for emp in emprestimos:
            info = ''
            emp: m.Emprestimo
            if emp.necessita_renovar():
                if emp.renovar():
                    info = 'Renovado agora'
                else:
                    info = 'Não é possível renovar, verificar no site'
            elif emp.esta_atrasado():
                info = 'Está atrasado'
            else:
                info = 'Não necessita de renovação'
            self.consulta.inserir_info(emp, info)

    def esquecer_login(self):
        """
        Apaga os dados salvos de login.
        """

        try:
            self.persistencia_dados.deletar_dados()
            self.consulta.show_deletado_sucesso()
        except PermissionError:
            messagebox.showwarning(
                "Autore9: ERRO DE PERMISSÃO",
                message="Erro de permissão ao apagar dados")
