import urllib.request
import urllib.parse

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
