# webcrawler_TJMG
Webcrawler para sentenças na plataforma do TJMG utilizando selenium+python


Configurações na funcao set_params():


# O web scraping utiliza a "Pesquisa Livre"

## Palavras: Lista de palavras para a busca
  Ex:
    palavras = " ".join(["Lista de palavras","para","a","busca"])

## Contendo:
  1 = todas as palavras
  2 = qualquer palavra
  3 = frase exata
  Ex:   
    contendo = 3

## Comarca: Nome da comarca, se estiver vazio "" seleciona todas as comarcas na busca
  Ex:
    comarca = "Mariana"

## Orgao Julgador: Nome do orgao julgador se estiver vazio "" seleciona todos os orgaos julgadores na busca
  Ex:
    orgao_julgador = "2ª CÍVEL/CRIME/VEC"
