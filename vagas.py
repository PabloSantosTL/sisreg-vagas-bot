import re
import time
import os
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
import threading
import itertools

loading = False

def spinner(msg="Carregando"):
    for c in itertools.cycle(["|", "/", "-", "\\"]):
        if not loading:
            break

        print(f"\r{msg} {c}", end="", flush=True)
        time.sleep(0.1)

    print("\r" + " " * 50 + "\r", end="")

# ===== CONFIGURAÇÕES LOGIN =====
usuario = "VAGAS-CERA1"
senha = "101010"

API_USER = "jose.almeida"
API_PASS = "gn6Z7tEogEU6GAHOQPRe"

BASE_API = "https://sisreg-es.saude.gov.br/solicitacao-ambulatorial-ms-tres-lagoas/_search"

BASE = "https://sisregiii.saude.gov.br"
start_url = BASE + "/cgi-bin/index#"

html_file = "vagas.html"


def carregar_codigos():
    auth = HTTPBasicAuth(API_USER, API_PASS)

    query = {
        "size": 1000,
        "sort": [{"codigo_solicitacao": "asc"}],
        "query": {
            "bool": {
                "must": [
                    {"term": {"codigo_central_reguladora": "500830"}},
                    {
                        "terms": {
                            "status_solicitacao.keyword": [
                                "SOLICITAÇÃO / PENDENTE / REGULADOR",
                                "SOLICITAÇÃO / PENDENTE / FILA DE ESPERA",
                                "SOLICITAÇÃO / REENVIADA / REGULADOR"
                            ]
                        }
                    }
                ]
            }
        },
        "_source": [
            "codigo_interno_procedimento",
            "descricao_interna_procedimento",
            "procedimentos.codigo_interno",
            "procedimentos.codigo_interno_procedimento",
            "procedimentos.descricao_interna"
        ]
    }

    codes = {}
    search_after = None

    while True:
        if search_after:
            query["search_after"] = [search_after]

        r = requests.post(BASE_API, json=query, auth=auth, timeout=30)
        r.raise_for_status()

        hits = r.json().get("hits", {}).get("hits", [])
        if not hits:
            break

        for h in hits:
            src = h.get("_source", {})

            procedimentos = src.get("procedimentos") or [{
                "codigo_interno_procedimento": src.get("codigo_interno_procedimento"),
                "descricao_interna": src.get("descricao_interna_procedimento")
            }]

            for p in procedimentos:
                codigo = str(
                    p.get("codigo_interno_procedimento") or
                    p.get("codigo_interno") or
                    src.get("codigo_interno_procedimento") or ""
                ).strip()

                nome = (
                    p.get("descricao_interna") or
                    src.get("descricao_interna_procedimento") or ""
                ).strip()

                if codigo and codigo not in codes:
                    codes[codigo] = nome

        search_after = hits[-1].get("sort", [None])[0]

        if len(hits) < 1000:
            break

        time.sleep(0.3)

    return list(codes.keys()), list(codes.values())


loading = True

t = threading.Thread(
    target=spinner,
    args=("Carregando procedimentos da API",)
)

t.start()

codes, nomes = carregar_codigos()

loading = False
t.join()

print(
    f"✓ {len(codes)} procedimentos carregados."
)

print("\n=== PROCEDIMENTOS COM PENDÊNCIA ===")
for i, (c, n) in enumerate(zip(codes, nomes), 1):
    print(f"{i:03d} | {c} | {n}")
print(f"\nTotal: {len(codes)}\n")


options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--log-level=3")

options.add_experimental_option(
    "excludeSwitches",
    ["enable-logging"]
)

service = Service(log_path="NUL")

driver = webdriver.Chrome(
    service=service,
    options=options
)

wait = WebDriverWait(driver, 20)

def login(usuario, senha):
    driver.get(start_url)

    inp_user = wait.until(EC.visibility_of_element_located((By.ID, "usuario")))
    inp_user.clear()
    inp_user.send_keys(usuario)

    inp_pass = wait.until(EC.visibility_of_element_located((By.ID, "senha")))
    inp_pass.clear()
    inp_pass.send_keys(senha)

    driver.find_element(By.XPATH, "//input[@value='entrar']").click()

    wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "f_principal")))
    driver.switch_to.default_content()


def load_in_iframe(path):
    iframe_src = BASE + path
    driver.switch_to.default_content()
    driver.execute_script(
        "var f=document.querySelector('iframe[name=\"f_principal\"]');"
        "if(!f)f=document.getElementById('f_main');"
        "if(f){f.src=arguments[0];}",
        iframe_src
    )
    try:
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "f_principal")))
        return True
    except TimeoutException:
        driver.switch_to.default_content()
        return False


def process_code(code):
    if not load_in_iframe("/cgi-bin/autorizador"):
        return None, None

    try:
        inp = wait.until(EC.visibility_of_element_located((By.NAME, "nu_procedimento")))
        inp.clear()
        inp.send_keys(code)
    except TimeoutException:
        return None, None

    try:
        driver.find_element(By.ID, "codProc_sia").click()
    except:
        pass

    driver.find_element(By.XPATH, "//input[@value='CONSULTAR']").click()
    time.sleep(0.8)

    try:
        driver.find_element(By.XPATH, "//*[contains(text(),'SOLICITAÇÕES INEXISTENTES')]")
        return 0, "sem fichas"
    except:
        pass

    qtd = 0
    try:
        el = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Solicitações (')]")))
        m = re.search(r"\((\d+)\)", el.text)
        if m:
            qtd = int(m.group(1))
    except:
        pass

    vaga = "sem vaga"

    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "tr.linha_selecionavel")
        row = next((r for r in rows if "TRES LAGOAS" in r.text.upper()), None)

        if row:
            driver.execute_script("arguments[0].click();", row)
            time.sleep(0.5)

            try:
                driver.find_element(By.XPATH, "//input[@value='A']").click()
                driver.find_element(By.XPATH, "//input[@value='APLICAR']").click()
            except:
                pass

            time.sleep(0.5)

            try:
                driver.find_element(By.XPATH, "//*[contains(text(),'NENHUMA VAGA ENCONTRADA')]")
            except:
                try:
                    val = driver.find_element(By.NAME, "horario").get_attribute("value")
                    vaga = val.split("|")[1]
                except:
                    vaga = "vaga encontrada"
    except:
        pass

    return qtd, vaga


def load_existing_html():
    data = {}

    if os.path.exists(html_file):
        with open(html_file, encoding="utf-8") as f:

            html = f.read()

            rows = re.findall(
                r"<tr>\s*"
                r"<td>(.*?)</td>\s*"
                r"<td>(.*?)</td>\s*"
                r"<td>(.*?)</td>\s*"
                r"<td.*?>(.*?)</td>\s*"
                r"<td>(.*?)</td>\s*"
                r"</tr>",
                html,
                re.DOTALL
            )

            for nome, codigo, fichas, vaga, verif in rows:
                data[codigo] = [nome, fichas, vaga, verif]

    return data


def save_html(data_dict):

    html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Vagas SISREG</title>

<style>

body{
    font-family:Arial,sans-serif;
    margin:20px;
    background:#f4f4f4;
}

h1{
    margin-bottom:15px;
}

input{
    width:100%;
    padding:10px;
    margin-bottom:15px;
    box-sizing:border-box;
}

table{
    width:100%;
    border-collapse:collapse;
    background:white;
}

th,td{
    padding:10px;
    border-bottom:1px solid #ddd;
}

th{
    background:#333;
    color:white;
    cursor:pointer;
    user-select:none;
}

tr:hover{
    background:#f5f5f5;
}

.sem-vaga{
    color:#888;
}

.com-vaga{
    color:green;
    font-weight:bold;
}

</style>

<script>

function searchTable(){

    let filtro =
        document.getElementById("search")
        .value
        .toUpperCase();

    document
        .querySelectorAll("tbody tr")
        .forEach(row => {

            row.style.display =
                [...row.cells]
                .some(c =>
                    c.innerText
                    .toUpperCase()
                    .includes(filtro)
                )
                ? ""
                : "none";
        });
}

function parseDate(txt){

    let m = txt.match(
        /(\\d{2})\\/(\\d{2})\\/(\\d{4})(?:\\s+(\\d{2}):(\\d{2}))?/
    );

    if(!m)
        return 0;

    return new Date(
        parseInt(m[3]),
        parseInt(m[2]) - 1,
        parseInt(m[1]),
        parseInt(m[4] || 0),
        parseInt(m[5] || 0)
    ).getTime();
}

function sortTable(col){

    const tbody =
        document.querySelector("tbody");

    const rows =
        Array.from(
            tbody.querySelectorAll("tr")
        );

    const asc =
        tbody.dataset.sort != col;

    rows.sort((a,b)=>{

        let va =
            a.cells[col].innerText.trim();

        let vb =
            b.cells[col].innerText.trim();

        if(col === 2){

            return asc
                ? Number(va)-Number(vb)
                : Number(vb)-Number(va);
        }

        if(col === 3){

            return asc
                ? parseDate(va)-parseDate(vb)
                : parseDate(vb)-parseDate(va);
        }

        return asc
            ? va.localeCompare(vb)
            : vb.localeCompare(va);
    });

    tbody.innerHTML = "";

    rows.forEach(r =>
        tbody.appendChild(r)
    );

    tbody.dataset.sort =
        asc ? col : "";
}

</script>

</head>

<body>

<h1>Vagas SISREG</h1>

<input
id="search"
placeholder="Buscar..."
onkeyup="searchTable()"
/>

<table>

<thead>
<tr>
<th onclick="sortTable(0)">Nome</th>
<th onclick="sortTable(1)">Código</th>
<th onclick="sortTable(2)">Fichas</th>
<th onclick="sortTable(3)">Data/Vaga</th>
<th onclick="sortTable(4)">Verificado</th>
</tr>
</thead>

<tbody>
"""

    for codigo, v in data_dict.items():

        classe = (
            "com-vaga"
            if "sem vaga" not in str(v[2]).lower()
            else "sem-vaga"
        )

        html += f"""
<tr>
<td>{v[0]}</td>
<td>{codigo}</td>
<td>{v[1]}</td>
<td class="{classe}">{v[2]}</td>
<td>{v[3]}</td>
</tr>
"""

    html += """
</tbody>
</table>
</body>
</html>
"""

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)


try:
    login(usuario, senha)

    resultados = load_existing_html()

    hoje = datetime.now().strftime("%d/%m")

    for i, code in enumerate(codes):

        nome = nomes[i]

        # Se já existe no HTML e foi verificado hoje, pula
        if code in resultados:

            ultima_verificacao = str(resultados[code][3])

            if ultima_verificacao.startswith(hoje):

                print(
                    f"\n[{i+1}/{len(codes)}] "
                    f"Pulando procedimento "
                    f"{code} - {nome} "
                    f"(já verificado hoje)"
                )

                continue

        while True:

            try:

                print(
                    f"\n[{i+1}/{len(codes)}] "
                    f"Analisando procedimento "
                    f"{code} - {nome}"
                )

                qtd, vaga = process_code(code)

                if qtd is None and vaga is None:
                    raise Exception(
                        "Possível CAPTCHA ou página não carregada."
                    )

                agora = datetime.now().strftime("%d/%m %H:%M")

                resultados[code] = [
                    nome,
                    str(qtd),
                    vaga,
                    agora
                ]

                print(
                    f"✓ Concluído | "
                    f"Fichas: {qtd} | "
                    f"Vaga: {vaga}"
                )

                save_html(resultados)

                break

            except Exception as e:

                print(
                    f"\n⚠ Erro ao processar "
                    f"{code} - {nome}"
                )

                print(f"Detalhes: {e}")

                print(
                    "\nResolva o CAPTCHA \n"
                    "acesse a pagina de consultas\n"
                    "e pressione ENTER no terminal para continuar."
                )

                input()

finally:
    driver.quit()
