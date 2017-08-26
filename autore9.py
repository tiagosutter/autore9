import argparse
import urllib.request
import urllib.parse
from getpass import getpass
from datetime import date, timedelta
import re
from html.parser import HTMLParser


class ParserEmprestimos(HTMLParser):
    """Analisa os dados da tabela HTML."""
    def __init__(self):
        HTMLParser.__init__(self)
        self.re_data = re.compile(r"\d{2}/\d{2}/\d{4}")
        self.dados = []
        self.re_url = re.compile(r"(?P<url>http://.*emprenova?.*)'")
        self.titulos = ['Código de empréstimo',
                        'Data de devolução prevista',
                        'Código de pubicação',
                        'Unidade',
                        'Tipo',
                        'Identificação',
                        'Referência',
                        'URL de renovação']

    def __iter__(self):
        self.corrigir_dados()
        pos_inicio = 0
        pos_fim = len(self.titulos)
        n_emprestimos = int(len(self.dados)/len(self.titulos))
        for emprestimo in range(n_emprestimos):
            chunk_emprestimo = self.dados[pos_inicio:pos_fim]
            dados_emprestimo = dict(zip(self.titulos, chunk_emprestimo))
            yield dados_emprestimo
            pos_inicio += len(self.titulos)
            pos_fim += len(self.titulos)

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag == "input" and "emprenova" in self.get_starttag_text():
            mo_url = self.re_url.search(self.get_starttag_text())
            url = mo_url.groupdict()['url']
            self.dados.append(url)

        if tag == "input" and "campoCad" in atributos.values():
            if atributos["value"].isdecimal():
                self.dados.append(atributos["value"])

    def handle_data(self, data):
        if self.lasttag == "td" and "grid" in self.get_starttag_text():
            self.dados.append(data)
        elif self.lasttag == "a" and self.re_data.match(data):
            self.dados.append(converter_em_date_obj(data))

    def corrigir_dados(self):
        """
        Verifica as posições onde a URL de renovação deveria estar
        e insere uma string vazia caso não haja URL de renovação.
        """
        pos_url = 7
        for pos in range(pos_url, len(self.dados), pos_url+1):
            if "emprenova" not in self.dados[pos] and self.dados[pos]:
                self.dados.insert(pos, "")
        if "emprenova" not in self.dados[-1] and self.dados[-1]:
            self.dados.append("")


def consulta(rgu, senha, url):
    """Faz a consulta e retorna o resultado html em uma string."""
    login_payload = dict(codinterno=rgu, senha=senha)
    encoded_login_payload = urllib.parse.urlencode(login_payload).encode()
    with urllib.request.urlopen(url, data=encoded_login_payload) as resposta:
        linhas_html = resposta.readlines()
    html = ""
    for linha in linhas_html:
        html += linha.strip().decode("iso-8859-1")

    # descarta as tags b, pois estavam tornando o parsing mais complexo
    html = html.replace("<b>", "")
    html = html.replace("</b>", "")

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

if __name__ == '__main__':
    parser_argumentos = argparse.ArgumentParser(description=None)
    parser_argumentos.add_argument("-fr", "--force-renew",
                                   help="tenta forçar a renovação "
                                   "independente da data",
                                   action="store_true")

    args = parser_argumentos.parse_args()

    rgu = int(input("Digite seu RGU: "))
    senha = getpass("Digite sua senha: ")

    resultado_consulta = consulta(rgu, senha, url_consulta)

    if "Senha Inválida" in resultado_consulta:
        print("Senha Inválida.")
    elif "Usuário não cadastrado" in resultado_consulta:
        print("Usuário não cadastrado.")

    parser_emprestimos = ParserEmprestimos()
    parser_emprestimos.feed(resultado_consulta)
    for emprestimo in parser_emprestimos:
        if necessita_renovar(emprestimo['Data de devolução prevista']) or \
           args.force_renew:
            if emprestimo['URL de renovação']:
                urllib.request.urlopen(emprestimo['URL de renovação'])
                print("Foi renovado com sucesso: ", emprestimo['Referência'])
            else:
                print("Não tem URL de renovação, favor verificar no site: ",
                      emprestimo['Referência'])
        else:
            print("Não necessita de renovação:",
                  emprestimo['Referência'],
                  "- data de devolução:",
                  emprestimo['Data de devolução prevista'])
