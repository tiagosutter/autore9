Autore9
=======
Script para renovar publicações emprestadas pela biblioteca da Universidade Católica de Petrópolis.

Funcionamento
-------------

Faz a consulta no site da biblioteca, caso falte 1 dia ou menos para a data de devolução de um emprestimo ele será renovado.

Requisito
---------
* Python 3

Funcionalidades
---------------
Chega de emprestimos atrasados!

* Renovação em caso de necessidade
* Capaz de salvar usuário e senha
* Capaz de forçar renovação de todos os emprestimos

Uso
---

* Uso mais simples:
  
  Solicita RGU e senha e renova as publicações se necessário.

  .. code-block:: bash

    $ python autore9.py
    $ Digite seu RGU: 11611051
    $ Digite sua senha:
    $ Você deseja salvar esses dados (S/N)?: N

  Caso escolha salvar os dados não será mais necessário digitar RGU e senha ao executar python autore9.py sem argumentos.
  Caso já tenha salvo e queira mudar RGU e senha utilize 

  .. code-block:: bash

    $ python autore9.py -e

Obtendo ajuda
-------------
  .. code-block:: bash

    $ python autore9.py --help
    usage: autore9.py [-h] [-fr] [-e]

    optional arguments:
      -h, --help          show this help message and exit
      -fr, --force-renew  tenta forçar a renovação independente da data
      -e, --esquecer      esquece rgu e senha salvos
