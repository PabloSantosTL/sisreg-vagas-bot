import re
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

usuario = ""
senha = ""

codes = []
nomes = []

BASE = "https://sisregiii.saude.gov.br"
START_URL = BASE + "/cgi-bin/index#"
HTML_FILE = "sisreg_resultado.html"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)


def login(usuario, senha):
	driver.get(START_URL)

	inp_user = wait.until(EC.visibility_of_element_located((By.ID, "usuario")))
	inp_user.clear()
	inp_user.send_keys(usuario)

	inp_pass = wait.until(EC.visibility_of_element_located((By.ID, "senha")))
	inp_pass.clear()
	inp_pass.send_keys(senha)

	btn = driver.find_element(By.XPATH, "//input[@type='button' and @value='entrar']")
	btn.click()

	wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "f_principal")))
	driver.switch_to.default_content()


def load_in_iframe(path):
	driver.switch_to.default_content()
	driver.execute_script(
		"var f=document.querySelector('iframe[name=\"f_principal\"]')||document.getElementById('f_main');"
		"if(f)f.src=arguments[0];",
		BASE + path,
	)
	wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "f_principal")))


def process_code(code):
	load_in_iframe("/cgi-bin/autorizador")

	inp = wait.until(EC.visibility_of_element_located((By.NAME, "nu_procedimento")))
	inp.clear()
	inp.send_keys(code)

	try:
		driver.find_element(By.ID, "codProc_sia").click()
	except Exception:
		try:
			driver.find_element(By.XPATH, "//input[@name='radio_codProc' and @value='interno']").click()
		except Exception:
			pass

	driver.find_element(By.XPATH, "//input[@type='button' and @value='CONSULTAR']").click()
	time.sleep(0.8)

	try:
		driver.find_element(By.XPATH, "//*[contains(text(),'SOLICITAÇÕES INEXISTENTES')]")
		driver.switch_to.default_content()
		return 0, "sem fichas"
	except NoSuchElementException:
		pass

	qtd = 0
	try:
		el = wait.until(
			EC.visibility_of_element_located(
				(By.XPATH, "//*[contains(text(),'Solicitações (') or contains(text(),'Solicitacoes (')]")
			)
		)
		m = re.search(r"\((\d+)\)", el.text)
		if m:
			qtd = int(m.group(1))
	except TimeoutException:
		pass

	data_vaga = "sem vaga"
	try:
		rows = driver.find_elements(By.CSS_SELECTOR, "tr.linha_selecionavel")
		row = next((r for r in rows if "TRES LAGOAS" in r.text.upper()), None)

		if row:
			driver.execute_script("arguments[0].click();", row)
			time.sleep(0.6)

			try:
				driver.find_element(By.XPATH, "//input[@name='status' and @value='A']").click()
			except Exception:
				pass

			try:
				driver.find_element(By.XPATH, "//input[@type='button' and @value='APLICAR']").click()
			except Exception:
				pass

			time.sleep(0.6)

			try:
				driver.find_element(By.XPATH, "//*[contains(text(),'NENHUMA VAGA ENCONTRADA')]")
			except NoSuchElementException:
				try:
					val = driver.find_element(By.NAME, "horario").get_attribute("value")
					parts = val.split("|")
					if len(parts) > 1:
						data_vaga = parts[1]
				except Exception:
					data_vaga = "vaga encontrada (sem data)"
		else:
			data_vaga = "sem ficha TRES LAGOAS"

	except Exception:
		pass

	driver.switch_to.default_content()
	return qtd, data_vaga


def load_existing_html():
	data = {}
	if os.path.exists(HTML_FILE):
		with open(HTML_FILE, encoding="utf-8") as f:
			rows = re.findall(
				r"<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>",
				f.read(),
			)
			for nome, codigo, fichas, vaga, verif in rows:
				data[codigo] = [nome, fichas, vaga, verif]
	return data


def save_html(data):
	html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>vagas SISREG</title>
<style>
body{font-family:Arial;margin:20px;background:#f4f4f4}
table{width:100%;border-collapse:collapse;background:#fff}
th,td{padding:10px;border-bottom:1px solid #ddd}
th{background:#333;color:#fff;cursor:pointer}
tr:hover{background:#f1f1f1}
input{width:100%;padding:8px;margin-bottom:12px}
</style>
<script>
function searchTable(){
	let f=document.getElementById("s").value.toUpperCase()
	document.querySelectorAll("tbody tr").forEach(r=>{
		r.style.display=[...r.cells].some(c=>c.innerText.toUpperCase().includes(f))?"":"none"
	})
}
</script>
</head>
<body>
<h1>vagas SISREG</h1>
<input id="s" onkeyup="searchTable()" placeholder="Buscar...">
<table>
<thead>
<tr><th>Nome</th><th>Código</th><th>Fichas</th><th>Data/Vaga</th><th>Verificado</th></tr>
</thead>
<tbody>
"""
	for codigo, (nome, fichas, vaga, verif) in data.items():
		html += f"<tr><td>{nome}</td><td>{codigo}</td><td>{fichas}</td><td>{vaga}</td><td>{verif}</td></tr>\n"

	html += "</tbody></table></body></html>"

	with open(HTML_FILE, "w", encoding="utf-8") as f:
		f.write(html)


try:
	login(usuario, senha)
	resultados = load_existing_html()

	for i, code in enumerate(codes):
		qtd, vaga = process_code(code)
		agora = datetime.now().strftime("%d/%m %H:%M")
		resultados[code] = [nomes[i], str(qtd), vaga, agora]
		save_html(resultados)

finally:
	driver.quit()