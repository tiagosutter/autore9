import argparse
import os
import pickle
import re
import urllib.parse
import urllib.request
from datetime import date, timedelta
from getpass import getpass

CAMINHO_ARQUIVO = os.path.abspath(os.sys.argv[0])
DIRETORIO_ARQUIVO = os.path.dirname(CAMINHO_ARQUIVO)
os.chdir(DIRETORIO_ARQUIVO)

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
MENSAGENS_DE_ERRO = ("Senha Inválida",
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
            dados = dict(zip(chaves, (data, url, titulo)))
            self.emprestimos.append(dados)



def consulta(rgu, senha, url):
    """Faz a consulta e retorna o resultado html em uma string."""
    login_payload = dict(codinterno=rgu, senha=senha)
    encoded_login_payload = urllib.parse.urlencode(login_payload).encode()
    with urllib.request.urlopen(url, data=encoded_login_payload) as resposta:
        linhas_html = resposta.readlines()
    html = ""
    for linha in linhas_html:
        html += linha.strip().decode("iso-8859-1")

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


def set_up_argparser():
    parser_argumentos = argparse.ArgumentParser(description=None)
    parser_argumentos.add_argument("-fr", "--force-renew",
                                   help="tenta forçar a renovação "
                                   "independente da data",
                                   action="store_true")
    parser_argumentos.add_argument("-e", "--esquecer",
                                   help="esquece rgu e senha salvos",
                                   action="store_true")

    argumentos = parser_argumentos.parse_args()
    return argumentos

if __name__ == '__main__':
    args = set_up_argparser()

    if args.esquecer and os.path.exists('.u_data'):
        os.remove('.u_data')

    if os.path.exists('.u_data'):
        with open('.u_data', 'rb') as f:
            rgu, senha = pickle.load(f)
    else:
        rgu = int(input("Digite seu rgu: "))
        senha = getpass("Digite sua senha: ")
        salvar = input("Você deseja salvar esses dados (S/N)?: ").lower()
        if salvar == "s":
            with open('.u_data', 'wb') as f:
                pickle.dump((rgu, senha), f)
            if 'win' in os.sys.platform:
                os.system("attrib .u_data +h")

    resultado_consulta = consulta(rgu, senha, URL_CONSULTA)
    erro = [mensagem for mensagem in MENSAGENS_DE_ERRO
            if mensagem in resultado_consulta]
    if erro:
        print("Erro: {}".format(erro[0]))
        if os.path.exists('.u_data') and erro in MENSAGENS_DE_ERRO[0:2]:
            os.remove('.u_data')
        input("Pressione ENTER para sair...")
        os.sys.exit()

    parser_emprestimos = ParserEmprestimos()
    parser_emprestimos.feed(resultado_consulta)
    for emprestimo in parser_emprestimos:
        if necessita_renovar(emprestimo['data']) or args.force_renew:
            if emprestimo['url']:
                urllib.request.urlopen(emprestimo['url'])
                print("Foi renovado com sucesso: ", emprestimo['titulo'])
            else:
                print("Não tem URL de renovação, favor verificar no site: ",
                      emprestimo['titulo'])
        elif esta_atrasado(emprestimo['data']):
            print("Não tem URL de renovação, pois a publicação está atrasada!",
                  emprestimo['titulo'])
        else:
            print("Não necessita de renovação:", emprestimo['titulo'],
                  "- Data de devolução prevista:",
                  emprestimo['data'].strftime("%d/%m/%Y"))
    input("Pressione ENTER para sair...")
