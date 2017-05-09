import urllib.request
import urllib.parse
from getpass import getpass
import re


def consulta(rgu, senha, url):
    """Faz a consulta e retorna o resultado html em uma string."""
    login_payload = dict(codinterno=rgu, senha=senha)
    encoded_login_payload = urllib.parse.urlencode(login_payload).encode()
    with urllib.request.urlopen(url, data=encoded_login_payload) as resposta:
        html = resposta.read().decode("iso-8859-1")
    return html


def get_datas_devolucao(html_consulta):
    """Retorna uma lista com as datas de devolução previstas"""
    datas = re.findall(r"\d{2}/\d{2}/\d{2}", html_consulta)
    return datas

url_base = 'http://200.20.252.54/informaweb/cgi-bin/iwmoduloleitor.dll/empcons?'

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
url_consulta = url_base + query_string

rgu = int(input("Digite seu RGU: "))
senha = getpass("Digite sua senha: ")

resultado_consulta = consulta(rgu, senha, url_consulta)

if "Senha Inválida" in resultado_consulta:
    print("Senha Inválida.")
elif  "Usuário não cadastrado" in resultado_consulta:
    print("Usuário não cadastrado.")
