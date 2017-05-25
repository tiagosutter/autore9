import urllib.request
import urllib.parse
from getpass import getpass
from datetime import date, timedelta
import re


def consulta(rgu, senha, url):
    """Faz a consulta e retorna o resultado html em uma string."""
    login_payload = dict(codinterno=rgu, senha=senha)
    encoded_login_payload = urllib.parse.urlencode(login_payload).encode()
    with urllib.request.urlopen(url, data=encoded_login_payload) as resposta:
        html = resposta.read().decode("iso-8859-1")
    return html


def get_datas_devolucao(html_consulta):
    """Retorna um iterador sobre objetos date com as datas de devolução."""
    re_datas = re.compile(r"(?P<dia>\d{2})/(?P<mes>\d{2})/(?P<ano>\d{4})")
    datas = re_datas.finditer(html_consulta)
    for data in datas:
        d = data.groupdict()
        ano, mes, dia = int(d['ano']), int(d['mes']), int(d['dia'])
        datetime_obj = date(ano, mes, dia)
        yield datetime_obj


def get_urls_renovacao(html_consulta):
    """Retorna uma lista com URLs relativos de renovação"""
    urls = re.findall(r"(emprenova\?.*?)'", html_consulta)
    return urls


def necessita_renovar(data_devolucao):
    """
    Retorna True caso falte 1 dia ou menos para a data de devolução prevista.
    """
    hoje = date.today()
    amanha = hoje + timedelta(1)
    return data_devolucao == amanha or data_devolucao == hoje

url_base = 'http://200.20.252.54/informaweb/cgi-bin/iwmoduloleitor.dll/'
pagina_consulta = '/empcons?'

# dados necessários para fazer consulta de emprestimos
query = {'bdbanco': 'InformaUCP',
         'g': 'web',
         'grupo': '***',
         'idSessao': '{C2B12B23-57F6-4FD9-A6CA-71D75901960A}',
         'idioma': 'POR',
         'rotina': 'EMP',
         'tipocons': 'EMPRESTIMO',
         'unidade': ''}

query_string = urllib.parse.urlencode(query)
url_consulta = url_base + pagina_consulta + query_string

rgu = int(input("Digite seu RGU: "))
senha = getpass("Digite sua senha: ")

resultado_consulta = consulta(rgu, senha, url_consulta)

if "Senha Inválida" in resultado_consulta:
    print("Senha Inválida.")
elif "Usuário não cadastrado" in resultado_consulta:
    print("Usuário não cadastrado.")
