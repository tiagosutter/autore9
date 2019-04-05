import re
import os.path
import pickle
import urllib.parse
from datetime import date
from datetime import timedelta

import requests


class ErroConsulta(Exception):
    """Representa um erro de consulta"""
    pass


class Biblioteca():
    _URL_BASE = 'http://200.20.252.54/informaweb/cgi-bin/iwmoduloleitor.dll/'
    _PAGINA_CONSULTA = '/empcons?'

    # dados necessários para fazer consulta de emprestimos
    _QUERY = {
         'bdbanco': 'InformaUCP',
         'g': 'web',
         'grupo': '***',
         'idSessao': '{C2B12B23-57F6-4FD9-A6CA-71D75901960A}',
         'idioma': 'POR',
         'rotina': 'EMP',
         'tipocons': 'EMPRESTIMO',
         'unidade': ''}

    _QUERY_STRING = urllib.parse.urlencode(_QUERY)
    _URL_CONSULTA = _URL_BASE + _PAGINA_CONSULTA + _QUERY_STRING
    _MENSAGENS_DE_ERRO = (
        "Não há campos preenchidos para a operação",
        "Campo de senha precisa ser digitado",
        "Senha Inválida",
        "Usuário não cadastrado",
        "Consulta sem resultado")

    @classmethod
    def consultar_emprestimo(cls, rgu: str, senha:str) -> str:
        login_payload = dict(codinterno=rgu, senha=senha)

        with requests.post(cls._URL_CONSULTA, data=login_payload) as resposta:
            html = resposta.text

        erro = [mensagem for mensagem in cls._MENSAGENS_DE_ERRO
                if mensagem in html]
        if erro:
            raise ErroConsulta(erro[0])

        return html


class PersistenciaDadosLogin():
    _ARQUIVO_DE_DADOS = '.u_data'

    def __init__(self):
        pass
    
    def existem_dados_salvos(self):
        """Verifica a existência de dados salvos.
        
        Returns:
            bool -- True caso existam dados salvos
        """
        return os.path.exists(self._ARQUIVO_DE_DADOS)

    def save_data(self, rgu: str, senha: str):
        """Persiste dados de login e senha.
        
        Arguments:
            rgu {str} -- RGU do aluno
            senha {str} -- Senha do aluno
        """
        with open(self._ARQUIVO_DE_DADOS, 'wb') as f:
            pickle.dump((rgu, senha), f)
        if 'win' in os.sys.platform:
            os.system("attrib " + self._ARQUIVO_DE_DADOS + " +h")

    def load_data(self):
        """Carrega os dados salvos.
        
        Returns:
            tuple -- (login, senha)
        """
        with open(self._ARQUIVO_DE_DADOS, 'rb') as f:
            return pickle.load(f)

    def deletar_dados(self):
        """Deleta os dados salvos"""
        os.remove(self._ARQUIVO_DE_DADOS)


class Emprestimo():
    """Classe para representar empréstimo"""

    def __init__(self, url_renovacao: str, data: date, titulo: str, **kwargs):
        """Inicializa o objeto.
        
        Arguments:
            url_renovacao {str} -- Url para renovação da publicação emprestada
            data {date} -- Data devolução prevista da publicação emprestada
            titulo {str} -- Título da publicação
        """
        self.url_renovacao = url_renovacao
        self.data = data
        self.autores = kwargs.get('autores', '')
        self.titulo = titulo
        self.isbn = kwargs.get('isbn', '')
    
    def __getitem__(self, key):
        return self.__dict__.get(key)

    def necessita_renovar(self):
        """
        Retorna True caso falte 1 dia ou menos para a data de devolução prevista.
        """
        hoje = date.today()
        amanha = hoje + timedelta(1)
        return self.data == amanha or self.data == hoje

    def esta_atrasado(self):
        """Retorna True caso a publicação esteja atrasada"""
        return self.data < date.today()

    def renovar(self):
        """Realiza a renovação quando possível.
        
        Returns:
            bool -- True caso a renovação seja executada com sucesso.
        """
        sucesso = False
        if self.url_renovacao:
            requests.get(self.url_renovacao)
            sucesso = True
        return sucesso


class ParserEmprestimos():
    """Analisa os dados do HTML."""

    def __init__(self):
        self.emprestimos = []
        self.re_table_emp = re.compile(r"<table class=\"grid\".*?</table>",
                                       re.DOTALL)
        self.re_table_row_emp = re.compile(r"<tr>.*?</tr>", re.DOTALL)

        self.re_data = re.compile(r"\d{2}/\d{2}/\d{4}")
        self.re_url = re.compile(r"(http://.*emprenova\?.*)'\"")
        self.re_referencia = re.compile(r"""
            width=\*>(?P<autores>.*)<b>
            (?P<titulo>.*)</b>
            (?P<mais>.*)
            """, re.VERBOSE)
        self.re_isbn = re.compile(r"ISBN (.*)\.")

    def __iter__(self) -> Emprestimo:
        for emp in self.emprestimos:
            yield emp

    def feed(self, html):
        """Faz a análise do HTML"""
        table = self.re_table_emp.search(html).group()
        tr_emprestimos = self.re_table_row_emp.finditer(table)
        for emp_row in tr_emprestimos:
            dados = self._get_dados_row(emp_row)
            obj_emprestimo = Emprestimo(**dados)
            self.emprestimos.append(obj_emprestimo)

    def _get_dados_row(self, emp_row):
        dados = {}

        table_row = emp_row.group()
        referencia = self.re_referencia.search(table_row).groupdict()
        dados['data'] = self._get_data(table_row)
        dados['url_renovacao'] = self._get_url_renovacao(table_row)
        dados['autores'] = referencia['autores']
        dados['titulo'] = referencia['titulo']
        dados['isbn'] = self._get_isbn(table_row)

        return dados

    def _get_url_renovacao(self, table_row):
        url = self.re_url.search(table_row)
        if url:
            url = url.group(1)
        return url

    def _get_data(self, table_row):
        """
        Retorna um objeto date criado a partir de uma string com data
        no formato dia/mês/ano.
        """
        str_data = self.re_data.search(table_row).group()
        re_data = re.compile(r"(?P<dia>\d{2})/(?P<mes>\d{2})/(?P<ano>\d{4})")
        mo_data = re_data.match(str_data)
        data_dict = mo_data.groupdict()
        ano = int(data_dict['ano'])
        mes = int(data_dict['mes'])
        dia = int(data_dict['dia'])
        return date(ano, mes, dia)

    def _get_isbn(self, table_row):
        isbn = self.re_isbn.search(table_row)
        if isbn:
            digitos_isbn = [c for c in isbn.group(1) if c.isdigit()]
            isbn = ''.join(digitos_isbn)
        return isbn
