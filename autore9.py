import os
import re
import pickle
import urllib.parse
from datetime import date, timedelta

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import requests

CAMINHO_ARQUIVO = os.path.abspath(os.sys.argv[0])
DIRETORIO_ARQUIVO = os.path.dirname(CAMINHO_ARQUIVO)
os.chdir(DIRETORIO_ARQUIVO)

ARQUIVO_DE_DADOS = '.u_data'

URL_BASE = 'http://200.20.252.54/informaweb/cgi-bin/iwmoduloleitor.dll/'
PAGINA_CONSULTA = '/empcons?'

# dados necessários para fazer consulta de emprestimos
QUERY = {'bdbanco': 'InformaUCP',
         'g': 'web',
         'grupo': '***',
         'idSessao': '{C2B12B23-57F6-4FD9-A6CA-71D75901960A}',
         'idioma': 'POR',
         'rotina': 'EMP',
         'tipocons': 'EMPRESTIMO',
         'unidade': ''}

QUERY_STRING = urllib.parse.urlencode(QUERY)
URL_CONSULTA = URL_BASE + PAGINA_CONSULTA + QUERY_STRING
MENSAGENS_DE_ERRO = (
    "Não há campos preenchidos para a operação",
    "Campo de senha precisa ser digitado",
    "Senha Inválida",
    "Usuário não cadastrado",
    "Consulta sem resultado")


class ParserEmprestimos():
    """Analisa os dados da tabela HTML."""

    def __init__(self):
        self.emprestimos = []
        self.re_table_emp = re.compile(r"<table class=\"grid\".*?</table>",
                                       re.DOTALL)
        self.re_table_row_emp = re.compile(r"<tr>.*?</tr>", re.DOTALL)
        self.re_data = re.compile(r"\d{2}/\d{2}/\d{4}")
        self.re_url = re.compile(r"(http://.*emprenova\?.*)'\"")
        self.re_referencia = re.compile(r"""
            width=\*>(.*)<b>   # Autor(es)
            (.*)</b>           # Título
            (.*)               # Subtítulo e mais
            """, re.VERBOSE)
        self.re_isbn = re.compile(r"ISBN (.*)\.")

    def __iter__(self):
        for emp in self.emprestimos:
            yield emp

    def feed(self, html):
        """Alimenta o parser"""
        table = self.re_table_emp.search(html).group()
        tr_emprestimos = self.re_table_row_emp.finditer(table)
        chaves = ("data", "url", "titulo")
        for emp in tr_emprestimos:
            table_row = emp.group()
            str_data = self.re_data.search(table_row).group()
            data = converter_em_date_obj(str_data)
            url = self.re_url.search(table_row)
            if url:
                url = url.group(1)
            titulo = self.re_referencia.search(table_row).group(2)
            isbn = self.re_isbn.search(table_row)
            if isbn:
                digitos_isbn = [c for c in isbn.group(1) if c.isdigit()]
                isbn = ''.join(digitos_isbn)
            dados = dict(zip(chaves, (data, url, titulo, isbn)))
            self.emprestimos.append(dados)


def consulta(rgu, senha, url):
    """Faz a consulta e retorna o resultado html em uma string."""
    login_payload = dict(codinterno=rgu, senha=senha)

    with requests.post(url, data=login_payload) as resposta:
        html = resposta.text

    return html


def converter_em_date_obj(data_br):
    """
    Retorna um objeto date criado a partir de uma string com data
    no formato dia/mês/ano.
    """
    re_data = re.compile(r"(?P<dia>\d{2})/(?P<mes>\d{2})/(?P<ano>\d{4})")
    mo_data = re_data.match(data_br)
    data_dict = mo_data.groupdict()
    ano = int(data_dict['ano'])
    mes = int(data_dict['mes'])
    dia = int(data_dict['dia'])
    return date(ano, mes, dia)


def necessita_renovar(data_devolucao):
    """
    Retorna True caso falte 1 dia ou menos para a data de devolução prevista.
    """
    hoje = date.today()
    amanha = hoje + timedelta(1)
    return data_devolucao == amanha or data_devolucao == hoje


def esta_atrasado(data_devolucao):
    """Retorna True caso a publicação esteja atrasada"""
    return data_devolucao < date.today()


def save_data(filename, rgu, senha):
    """Salva dados para arquivo"""
    with open(filename, 'wb') as f:
        pickle.dump((rgu, senha), f)
    if 'win' in os.sys.platform:
        os.system("attrib " + ARQUIVO_DE_DADOS + " +h")


def load_data(filename):
    """Carrega dados salvos"""
    with open(filename, 'rb') as f:
        return pickle.load(f)


class LoginFormFrame(tk.Frame):
    """Formulário de login"""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.senha_var = tk.StringVar()
        self.rgu_var = tk.StringVar()
        rgu_label = ttk.Label(self, text="RGU: ")
        rgu_label.grid(row=0, column=0, sticky=(tk.E + tk.W))
        senha_label = ttk.Label(self, text="Senha: ")
        senha_label.grid(row=1, column=0, sticky=(tk.E + tk.W))

        comando_validar_rgu = (self.register(self._validar_digito), '%P')
        rgu_entry = ttk.Entry(self, textvariable=self.rgu_var)
        rgu_entry.grid(row=0, column=1, pady=5, padx=5)
        rgu_entry.config(validate='key', validatecommand=comando_validar_rgu)
        rgu_entry.focus_set()

        self.senha_entry = ttk.Entry(self, show='*',
                                     textvariable=self.senha_var)
        self.senha_entry.grid(row=1, column=1, pady=5, padx=5)

        rgu_entry.bind('<Return>', lambda e: self.senha_entry.focus_set())

    def _validar_digito(self, proposed: str) -> bool:
        return proposed.isdigit()


class ConsultaFrame(tk.Frame):
    """Frame que mostra o resultado da consutla"""

    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        super().__init__(parent, *args, **kwargs)
        self.tree = ttk.Treeview(self, columns=['data', 'info'], height=5)
        self.tree.heading('#0', text='Título')
        self.tree.heading('data', text='Data de entrega prevista')
        self.tree.heading('info', text='Informação')

        self.btn_esquecer = ttk.Button(self, text="Esquecer meu login",
                                       command=self.esquecer)

    def show(self, resultado):
        """Exibe os resutlados da consulta em tabela"""
        parser = ParserEmprestimos()
        parser.feed(resultado)
        for emp in parser:
            if(necessita_renovar(emp['data'])):
                if emp['url']:
                    requests.get(emp['url'])
                    info = 'Foi renovado com sucesso'
                else:
                    info = 'Não é possível renovar, verificar no site'
            else:
                info = "Não necessita de renovação"
            self.tree.insert(
                '',
                'end',
                text=emp['titulo'],
                values=(emp['data'].strftime("%d/%m/%Y"), info)
            )
        self.tree.grid()
        if os.path.exists(ARQUIVO_DE_DADOS):
            self.btn_esquecer.grid(row=1, column=0, sticky=tk.E)
        self.tkraise()

    def esquecer(self):
        """Deleta os dados salvos"""
        try:
            os.remove(ARQUIVO_DE_DADOS)
            self.btn_esquecer.grid_forget()
            label = ttk.Label(self, text='Dados de login removidos')
            label.grid()
        except PermissionError:
            messagebox.showwarning(
                "Autore9: ERRO DE PERMISSÃO",
                message="Erro de permissão ao apagar dados")


class Application(tk.Tk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Autore9")
        self.geometry('250x130')
        self.resizable(height=False, width=False)

        self.consulta = ConsultaFrame(self)
        self.consulta.grid(row=0, column=0)
        self.login_form = LoginFormFrame(self)
        self.login_form.grid(row=0, column=0)

        self.login_form.senha_entry.bind('<Return>', self.login)

        self.salvar = tk.IntVar()
        self.chkbox_save = ttk.Checkbutton(self, text='Lembrar de mim',
                                           variable=self.salvar)
        self.chkbox_save.grid(row=1, column=0, pady=5)

        self.enter_button = ttk.Button(self, command=self.login, text="Entrar")
        self.enter_button.grid(row=2, column=0, pady=5)

        self.columnconfigure(0, weight=1)
        if os.path.exists(ARQUIVO_DE_DADOS):
            self.lembrar_login()

    def salvar_login(self, rgu, senha):
        """Salva os dados do formulário para arquivo"""
        try:
            save_data(ARQUIVO_DE_DADOS, rgu, senha)
        except PermissionError:
            messagebox.showwarning(
                "Autore9: ERRO DE PERMISSÃO",
                message="Erro de permissão ao salvar dados")

    def lembrar_login(self):
        """Carrega o arquivo com dados do usuário"""
        try:
            rgu, senha = load_data(ARQUIVO_DE_DADOS)
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

        try:
            resultado_consulta = consulta(rgu, senha, URL_CONSULTA)
            erro = [mensagem for mensagem in MENSAGENS_DE_ERRO
                    if mensagem in resultado_consulta]
        except requests.ConnectionError:
            erro = ['Erro de conexão']

        if erro:
            messagebox.showerror("Autore9: ERRO NA CONSULTA", message=erro[0])
        else:
            self.geometry('')
            self.login_form.grid_forget()
            self.enter_button.grid_forget()
            self.chkbox_save.grid_forget()
            self.consulta.show(resultado_consulta)
            if self.salvar.get() == 1:
                self.salvar_login(rgu, senha)


if __name__ == '__main__':
    app = Application()
    app.mainloop()
