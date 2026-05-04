#!/usr/bin/env python3
"""
Scraper para extrair paróquias e horários de missas da Arquidiocese de Campo Grande.

Uso:
    python scraper_arqcgr.py

Saídas geradas no diretório atual:
    - paroquias_arqcgr.json   (dados estruturados)
    - paroquias_arqcgr.csv    (um horário por linha, fácil de abrir no Excel)

Dependências:
    pip install requests beautifulsoup4 lxml
"""

import csv
import json
import re
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://arquidiocesedecampogrande.org.br"
LIST_URL = f"{BASE_URL}/nossas-paroquias/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

# Tempo entre requisições para não sobrecarregar o servidor
DELAY_BETWEEN_REQUESTS = 1.5  # segundos


def fetch(url: str, retries: int = 3, timeout: int = 30) -> str:
    """Faz GET com retentativas e retorna o HTML em texto."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            last_err = e
            print(f"  [tentativa {attempt}/{retries}] erro em {url}: {e}", file=sys.stderr)
            time.sleep(2 * attempt)
    raise RuntimeError(f"Falhou após {retries} tentativas: {url} ({last_err})")


def listar_paroquias() -> list[dict]:
    """Lê a página de Nossas Paróquias e devolve [{nome, url}, ...]."""
    print(f"==> Lendo lista de paróquias: {LIST_URL}")
    html = fetch(LIST_URL)
    soup = BeautifulSoup(html, "lxml")

    paroquias: list[dict] = []
    vistos: set[str] = set()

    # As paróquias são links cujo href contém "/paroquias/"
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/paroquias/" not in href:
            continue
        # Precisa ser uma URL que aponta pra uma paróquia específica, não a listagem
        if href.rstrip("/").endswith("/paroquias") or href.rstrip("/").endswith("/nossas-paroquias"):
            continue

        url = urljoin(BASE_URL, href).rstrip("/") + "/"
        # Texto do link geralmente contém o nome. Mas muitos links são do tipo imagem/botão.
        nome = a.get_text(strip=True)
        if not nome:
            continue
        # Ignora nomes genéricos tipo "Saiba mais"
        if len(nome) < 8:
            continue
        # Deduplica por URL
        if url in vistos:
            continue
        vistos.add(url)
        paroquias.append({"nome": nome, "url": url})

    print(f"    {len(paroquias)} paróquias encontradas.")
    return paroquias


def extrair_celebracoes(soup: BeautifulSoup) -> list[dict]:
    """
    Localiza a tabela 'Horário das celebrações' e devolve lista de dicts:
    {tipo, dia, horario, observacoes}.
    """
    celebracoes: list[dict] = []

    for tabela in soup.find_all("table"):
        linhas = tabela.find_all("tr")
        if not linhas:
            continue

        # Cabeçalho: procura por "Tipo", "Dia", "Horário"
        cabec = [c.get_text(strip=True).lower() for c in linhas[0].find_all(["th", "td"])]
        if not any("tipo" in c for c in cabec):
            continue
        if not any("hor" in c for c in cabec):
            continue

        for linha in linhas[1:]:
            colunas = [c.get_text(" ", strip=True) for c in linha.find_all(["td", "th"])]
            if len(colunas) < 3:
                continue
            tipo = colunas[0]
            dia = colunas[1]
            horario = colunas[2]
            obs = colunas[3] if len(colunas) >= 4 else ""
            if not (tipo or dia or horario):
                continue
            celebracoes.append(
                {
                    "tipo": tipo,
                    "dia": dia,
                    "horario": horario,
                    "observacoes": obs,
                }
            )

    return celebracoes


def extrair_info_paroquia(soup: BeautifulSoup) -> dict:
    """Extrai informações adicionais da paróquia: forania, endereço, telefone, e-mail."""
    info: dict = {
        "forania": "",
        "endereco": "",
        "telefone": "",
        "email": "",
        "ano_criacao": "",
    }

    # O site usa uma estrutura de listas com rótulos fixos.
    texto = soup.get_text("\n", strip=True)

    # Forania (vem logo após a palavra "Forania")
    m = re.search(r"Forania\s*\n+\s*([^\n]+)", texto)
    if m:
        info["forania"] = m.group(1).strip()

    # Ano de criação
    m = re.search(r"Ano\s+da\s+cria[cç][aã]o\s*\n+\s*([^\n]+)", texto, re.IGNORECASE)
    if m:
        info["ano_criacao"] = m.group(1).strip()

    # E-mail
    m = re.search(r"[\w.\-+]+@[\w\-]+\.[\w\.\-]+", texto)
    if m:
        info["email"] = m.group(0)

    # Telefone
    m = re.search(r"\(\d{2}\)\s*\d{4,5}[-\s]?\d{4}", texto)
    if m:
        info["telefone"] = m.group(0)

    # Endereço: seção "Endereço" até o próximo rótulo
    m = re.search(
        r"Endere[cç]o\s*\n+(.+?)(?:\n(?:Como Chegar|Hor[aá]rio|Clero|Site|Redes Sociais))",
        texto,
        re.DOTALL,
    )
    if m:
        info["endereco"] = " ".join(line.strip() for line in m.group(1).splitlines() if line.strip())

    return info


def extrair_dados_paroquia(nome: str, url: str) -> dict:
    html = fetch(url)
    soup = BeautifulSoup(html, "lxml")
    # Remove scripts/estilos para limpar o texto
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    info = extrair_info_paroquia(soup)
    celebracoes = extrair_celebracoes(soup)

    return {
        "nome": nome,
        "url": url,
        **info,
        "celebracoes": celebracoes,
    }


def salvar_json(dados: list[dict], caminho: str = "paroquias_arqcgr.json") -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"==> JSON salvo em: {caminho}")


def salvar_csv(dados: list[dict], caminho: str = "paroquias_arqcgr.csv") -> None:
    """Um horário por linha — melhor formato para análise no Excel."""
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "Paróquia",
                "Forania",
                "Endereço",
                "Telefone",
                "E-mail",
                "Tipo",
                "Dia da Semana",
                "Horário",
                "Observações",
                "URL",
            ]
        )
        for p in dados:
            celebracoes = p.get("celebracoes") or [{}]
            for c in celebracoes:
                writer.writerow(
                    [
                        p["nome"],
                        p.get("forania", ""),
                        p.get("endereco", ""),
                        p.get("telefone", ""),
                        p.get("email", ""),
                        c.get("tipo", ""),
                        c.get("dia", ""),
                        c.get("horario", ""),
                        c.get("observacoes", ""),
                        p["url"],
                    ]
                )
    print(f"==> CSV salvo em: {caminho}")


def main() -> None:
    paroquias = listar_paroquias()
    resultados: list[dict] = []

    for i, p in enumerate(paroquias, start=1):
        print(f"[{i}/{len(paroquias)}] {p['nome']}")
        try:
            dados = extrair_dados_paroquia(p["nome"], p["url"])
            resultados.append(dados)
            ncel = len(dados["celebracoes"])
            print(f"    {ncel} celebrações extraídas")
        except Exception as e:
            print(f"    ERRO: {e}", file=sys.stderr)
            resultados.append(
                {
                    "nome": p["nome"],
                    "url": p["url"],
                    "erro": str(e),
                    "celebracoes": [],
                }
            )
        time.sleep(DELAY_BETWEEN_REQUESTS)

    salvar_json(resultados)
    salvar_csv(resultados)

    total_cel = sum(len(p.get("celebracoes", [])) for p in resultados)
    print(
        f"\n==> Concluído! {len(resultados)} paróquias, {total_cel} celebrações no total."
    )


if __name__ == "__main__":
    main()
