import os
import shutil
import time
from datetime import date
import glob

import pandas as pd
import speech_recognition as sr

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as exception
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


def set_params():

    # O web scraping utiliza a "Pesquisa Livre"

    # palavras = Lista de palavras para a busca
    palavras = " ".join(["Lista de palavras","para","a","busca"])

    ## contendo:
    #1 = todas as palavras
    #2 = qualquer palavra
    #3 = frase exata

    contendo = 3

    ## comarca = Nome da comarca, se estiver vazio "" seleciona todas as comarcas na busca
    comarca = "Mariana"
    ##Orgao Julgador= Nome do orgao julgador se estiver vazio "" seleciona todos os orgaos julgadores na busca
    orgao_julgador = "2ª CÍVEL/CRIME/VEC"

    return [palavras, contendo, comarca, orgao_julgador]

# inicializa projeto
download_path = ""
def inicializa_projeto():
    global download_path
    download_path = os.getcwd() +"/downloads"
    if not os.path.exists(download_path):
        os.mkdir(download_path)
    if not os.path.exists("./registros"):
        os.mkdir("./registros")

def inicializa_driver():
    global download_path

    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory" : download_path}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=options)
    driver.maximize_window()
    return driver


def check_exists_by_CSS_SELECTOR(driver,css_selector):
    try:
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR,css_selector)
    except  exception.NoSuchElementException:
        return False
    except exception.StaleElementReferenceException:
        return False
    return True

def resolve_captcha_audio(driver):
    try:
        global contador_captcha
        global download_path
        if check_exists_by_CSS_SELECTOR(driver, "#linkCaptcha"):

            path = f"{download_path}/audio.wav"
            driver.find_element(By.LINK_TEXT,"Baixar o áudio").click()

            time.sleep(1)

            with sr.AudioFile(path) as source:
                audio = sr.Recognizer().record(source)

            captcha_field = driver.find_element(By.ID, "captcha_text")
            numeros = sr.Recognizer().recognize_google(audio, language='pt-BR')
            numeros = str(numeros).replace(" ","")

            if len(numeros)<5:
                driver.find_element(By.LINK_TEXT,"Gerar nova imagem").click()
                os.remove(path)
                resolve_captcha_audio(driver)
            elif not numeros.isnumeric():
                driver.find_element(By.LINK_TEXT,"Gerar nova imagem").click()
                os.remove(path)
                resolve_captcha_audio(driver)

            captcha_field.send_keys(numeros)
            os.remove(path)

            time.sleep(3)
            resolve_captcha_audio(driver)
    except exception.StaleElementReferenceException:
        pass

def pagina_pesquisa(driver):
    params = set_params()
    driver.get("https://www5.tjmg.jus.br/jurisprudencia/sentenca.do")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "palavrasConsulta"))) \
        .send_keys(params[0])
    driver.find_element(By.CSS_SELECTOR, "#resultPagina > option:nth-child(1)").click()
    driver.find_element(By.ID, "tipoFiltro" + str(params[1])).click()

    if params[2]!= "":
        comarcas = driver.find_elements(By.CSS_SELECTOR, "#codigoComarca option")

        for comarca in comarcas:
            if comarca.text == params[2]:
                comarca.click()

    if params[3]!= "":
        orgaosJulgadores = driver.find_elements(By.CSS_SELECTOR, "#codigoOrgaoJulgador option")

        for orgaosJulgador in orgaosJulgadores:
            if orgaosJulgador.text == params[3]:
                orgaosJulgador.click()

    driver.find_element(By.ID, "pesquisar").click()

def proxima_pagina(driver):
    try:
        botao_proximo = driver.find_element(By.XPATH, '//*[@id="tabelaSentenca"]/table/tbody/tr/td[1]/form/input[17]')
        botao_proximo.click()
        resolve_captcha_audio(driver)
        return True
    except exception.NoSuchElementException:
        return False

def get_day_time():
    return str(date.today()) + "_" + "_".join(time.asctime().split(" ")[-2].split(":"))

def trocar_aba(driver, close=False):
    p = driver.current_window_handle
    chwd = driver.window_handles
    for w in chwd:
        if w != p:
            driver.switch_to.window(w)
    if close:
        p = driver.current_window_handle
        chwd = driver.window_handles
        for w in chwd:
            if w != p:
                driver.switch_to.window(w)
                driver.close()
            driver.switch_to.window(p)


def ler_processo_pagina1(driver, atributos):
    while(True):
        try:
            ###############################################################################
            #################   CLASSE  #######################
            ###############################################################################

            classe = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "campoClasse"))).text
            # classe = driver.find_element(By.ID, "campoClasse").text
            atributos.append(classe)

            ###############################################################################
            #################   ASSUNTO  #######################
            ###############################################################################

            assunto = driver.find_element(By.CSS_SELECTOR,
                                          "body > table:nth-child(22) > tbody > tr:nth-child(2) > td:nth-child(2)").text
            assunto = "-".join(assunto.split(">")[-2:])
            atributos.append(assunto)

            ###############################################################################
            #################   PARTES  #######################
            ###############################################################################

            partes = driver.find_elements(By.CSS_SELECTOR, "#partes td")
            text_partes = dict()
            for i in range(0, len(partes), 2):
                text_partes[partes[i].text.replace(":", "").replace(" ", "")] = partes[i + 1].text

            atributos.append(text_partes)
            return atributos
        except Exception:
            resolve_captcha_audio(driver)


def ler_processo_pagina2(driver, atributos):
    while(True):
        try:
            ###############################################################################
            #################   SENTENCA  #######################
            ###############################################################################

            sentencas = list()
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".corpo")))

            sentencas_elements = driver.find_elements(By.CSS_SELECTOR, "td a")
            for sentenca_element in sentencas_elements:
                if "javascript" not in sentenca_element.get_property("href"):
                    sentencas.append(sentenca_element.get_property("href"))

            atributos.append(sentencas)

            ###############################################################################
            #################   SITUACAO SENTENCA  #######################
            ###############################################################################

            situacoes_sentenca = list()

            situacoes_elements = driver.find_elements(By.CSS_SELECTOR, "body > table.corpo > tbody > tr > td:nth-child(2)")
            for situacao_element in situacoes_elements:
                situacao = situacao_element.text
                if "sentença" in situacao.lower() or \
                        "julgado" in situacao.lower() or \
                        "extinto" in situacao.lower() or \
                        "homologada a transação" in situacao.lower() or \
                        "embargos de declaração não acolhida" in situacao.lower():
                    if "trânsito" not in situacao.lower() and "transitado" not in situacao.lower():
                        situacoes_sentenca.append(situacao)

            atributos.append(situacoes_sentenca)

            ###############################################################################
            #################   DATA ORIGEM  #######################
            ###############################################################################

            movimentaocoes_elements = driver.find_elements(By.CSS_SELECTOR, ".corpo .linha1 td, .corpo .linha2 td")
            origem = movimentaocoes_elements[-1].text.split("/")[-1]

            atributos.append(origem)
            return atributos
        except Exception:
            resolve_captcha_audio(driver)

count_processo = 0
def ler_processo(driver):
    global count_processo
    count_processo = count_processo +1
    print("Ler Processo: ", count_processo)

    atributos = list()

    trocar_aba(driver)

    atributos = ler_processo_pagina1(driver,atributos)


    ###############################################################################

    driver.find_element(By.CSS_SELECTOR, "body > table:nth-child(29) > tbody > tr > td:nth-child(2) > b > a").click()
    resolve_captcha_audio(driver)

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "corpo")))

    atributos = ler_processo_pagina2(driver, atributos)

    ###############################################################################
    trocar_aba(driver, close=True)

    return atributos

def ler_pagina(driver):

    while(True):
        resolve_captcha_audio(driver)
        ###############################################################################
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "tabelaSentenca")))

        processos = driver.find_elements(By.CSS_SELECTOR, "#tabelaSentenca .linkListaEspelhoAcordaos")

        ###############################################################################

        processos_pagina = list()
        for processo in processos:
            processo_info = list()
            numeros_processo = processo.find_elements(By.CSS_SELECTOR, "div")

            for numero in numeros_processo:
                processo_info.append(numero.text)

            numeros_processo[0].click()
            attemps =0
            while attemps<2:
                resultado = ler_processo(driver)
                if not resultado==False:
                    processo_info.extend(resultado)
                    break
                else:
                    attemps = + 1

            ###############################################################################

            processo_info.append(processo.get_property("href"))

            processos_pagina.append(processo_info)

        return processos_pagina

def ler_paginas(driver):
    lista_processo_info = list()
    nomes_colunas = ["Numero_tjmg", "Numero_pje", "Classe", "Assunto", "Partes", "Sentenca", "Situacao", "Data Origem", "Link_TJMG"]

    # while (True):
    for i in range(2):
        pagina = ler_pagina(driver)
        lista_processo_info.extend(pagina)
        salvar_temporario(nomes_colunas, pagina)
        if not proxima_pagina(driver):
            break

def salvar_tabelas():
    all_filenames = [i for i in glob.glob(f'./registros/temporario/*.csv')]
    combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames])
    combined_csv.to_csv(f"./registros/lista_processos_{get_day_time()}.csv", index=None)


def salvar_temporario(nomes_colunas, lista_processo_info):
    df_processo_info = pd.DataFrame(lista_processo_info, columns=nomes_colunas)
    outdir = './registros/temporario/'
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    df_processo_info.to_csv(f"{outdir}/lista_processos_{get_day_time()}.csv", index=None)


def limpar_projeto():
    global download_path
    if os.path.exists("./registros/temporario"):
        shutil.rmtree("./registros/temporario")
    if os.path.exists(download_path):
        shutil.rmtree(download_path)


if __name__ == '__main__':
    limpar_projeto()
    inicializa_projeto()
    driver = inicializa_driver()
    try:
        pagina_pesquisa(driver)
        ler_paginas(driver)
    finally:
        salvar_tabelas()
        limpar_projeto()
        driver.quit()
