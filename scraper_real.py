#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper Real de Imóveis em Cascavel/PR — v3.1
Abordagem: busca pelos links href*="/imovel/" (VivaReal/Zap)
e filtra cards da OLX pelo href contendo "regiao-de-cascavel".
"""

# Títulos que indicam navegação/publicidade — NÃO são imóveis reais
TITULO_BLACKLIST = {
    "venda - casas e apartamentos",
    "publicidade",
    "super destaque",
    "aluguel - casas e apartamentos",
    "anunciar imóveis",
    "criar alerta",
    "ordenar por",
    "imóveis à venda",
    "encontre imóveis",
    "todos os imóveis",
    "ver mais imóveis",
}

MIN_TITULO_LEN = 15       # títulos com menos caracteres são descartados
MAX_PRECO_PLAUSIVEL = 30_000_000   # acima disso é provável lixo de navegação

import asyncio
import json
import re
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "imoveis.json"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def load_existing() -> list:
    if DATA_PATH.exists():
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save(properties: list):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(properties, f, ensure_ascii=False, indent=2)


def make_id(url: str, title: str) -> str:
    raw = f"{url}|{title}"
    return hashlib.md5(raw.encode()).hexdigest()[:14]


def to_float(price_str: str) -> float:
    if not price_str:
        return 0.0
    cleaned = re.sub(r"[^\d]", "", price_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def to_int(s: str) -> int:
    m = re.search(r"\d+", s or "")
    return int(m.group()) if m else 0


def get_tipo(text: str) -> str:
    t = text.lower()
    if "apartamento" in t or "apto" in t: return "Apartamento"
    if "sobrado" in t: return "Sobrado"
    if "casa" in t: return "Casa"
    if "terreno" in t or "lote" in t: return "Terreno"
    if "sala" in t or "conjunto" in t: return "Comercial"
    return "Imóvel"


def titulo_valido(titulo: str) -> bool:
    """Rejeita títulos que são claramente itens de navegação ou publicidade."""
    if not titulo or len(titulo) < MIN_TITULO_LEN:
        return False
    t_lower = titulo.lower().strip()
    if t_lower in TITULO_BLACKLIST:
        return False
    if any(bad in t_lower for bad in [
        "publicidade", "super destaque", "venda - casas",
        "aluguel - casas", "anunciar", "criar alerta", "ordenar",
        "filtrar", "página", "resultados", "imóveis à venda em"
    ]):
        return False
    return True


def classify(bairro: str) -> str:
    from cascavel_regions_py import get_region
    return get_region(bairro)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# BROWSER SETUP
# ---------------------------------------------------------------------------

async def new_context(playwright):
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
    )
    ctx = await browser.new_context(
        viewport={"width": 1366, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
        extra_http_headers={
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )
    await ctx.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt']});
    """)
    return browser, ctx


# ---------------------------------------------------------------------------
# EXTRAI DADOS DE CARD VIA TEXTO COM REGEX
# ---------------------------------------------------------------------------

def parse_card_text(text: str, url: str, img: str, fonte: str) -> dict | None:
    """
    Extrai dados estruturados de um bloco de texto de card imobiliário.
    Funciona para VivaReal, ZapImóveis e OLX.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) < 3:
        return None

    # Preço: busca R$ seguido de número
    price_raw = ""
    preco = 0.0
    for line in lines:
        if "R$" in line or "r$" in line.lower():
            m = re.search(r"R\$\s*([\d.,]+)", line, re.IGNORECASE)
            if m:
                price_raw = m.group(0)
                preco = to_float(m.group(1).replace(".", "").replace(",", "."))
                break

    if preco <= 0:
        return None

    # Título: primeira linha com mais de 10 chars (que não seja preço nem spec)
    titulo = ""
    for line in lines:
        if len(line) > 10 and "R$" not in line and not re.match(r"^\d+\s*m[²2²]$", line, re.IGNORECASE):
            titulo = line
            break

    if not titulo:
        return None

    # Validar título — rejeitar navegação/publicidade
    if not titulo_valido(titulo):
        return None

    # Validar preço plausível (imóveis em Cascavel: R$50k a R$30M)
    if preco < 50_000 or preco > MAX_PRECO_PLAUSIVEL:
        return None

    # Bairro: busca "Bairro, Cascavel" ou "Cascavel, Bairro"
    bairro = "Cascavel"
    for line in lines:
        # Padrão: "Bairro, Cascavel" ou "Cascavel, Bairro, PR"
        m = re.match(r"^([^,\n]+),\s*Cascavel", line, re.IGNORECASE)
        if m:
            bairro = m.group(1).strip()
            break
        m = re.match(r"^Cascavel,\s*([^,\n]+)", line, re.IGNORECASE)
        if m:
            bairro = m.group(1).strip()
            break
        # Padrão OLX: "Cascavel, Bairro"
        if "cascavel" in line.lower() and "," in line:
            parts = [p.strip() for p in line.split(",")]
            idx = next((i for i, p in enumerate(parts) if "cascavel" in p.lower()), -1)
            if idx >= 0 and idx + 1 < len(parts):
                bairro = parts[idx + 1]
            elif idx > 0:
                bairro = parts[idx - 1]
            break

    # Specs: quartos, vagas, área
    quartos = vagas = area = 0
    for line in lines:
        if re.match(r"^\d+\s*m[²2]", line, re.IGNORECASE):
            area = to_int(line)
    # Regex no texto completo
    m = re.search(r"(\d+)\s*(?:quarto|dorm|bedroom)", text, re.IGNORECASE)
    if m: quartos = int(m.group(1))
    m = re.search(r"(\d+)\s*(?:vaga|garagem|garage|parking)", text, re.IGNORECASE)
    if m: vagas = int(m.group(1))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", text, re.IGNORECASE)
    if m: area = to_int(m.group(1).replace(",", ".").split(".")[0])

    # Endereço: linha com rua ou bairro+cascavel
    endereco = bairro + ", Cascavel/PR"
    for line in lines:
        if any(word in line.lower() for word in ["rua ", "av ", "avenida ", "alameda "]):
            endereco = line
            break

    return {
        "id": make_id(url, titulo),
        "titulo": titulo[:120],
        "tipo": get_tipo(titulo + " " + text),
        "preco": preco,
        "bairro": bairro[:50],
        "regiao": classify(bairro),
        "endereco": endereco[:150],
        "quartos": quartos,
        "suites": 0,
        "banheiros": max(1, quartos // 2) if quartos > 0 else 1,
        "vagas": vagas,
        "area_util": area,
        "area_total": area,
        "descricao": f"Imóvel à venda em {bairro}, Cascavel/PR. Dados obtidos via {fonte}.",
        "imagens": [img] if img and img.startswith("http") else [],
        "fonte": fonte,
        "url_original": url,
        "data_adicionado": now_iso(),
        "is_new": False,
    }


# ---------------------------------------------------------------------------
# VIVAREAL SCRAPER — busca por links /imovel/
# ---------------------------------------------------------------------------

async def scrape_vivareal(ctx) -> list:
    url = "https://www.vivareal.com.br/venda/parana/cascavel/?__vt=hl:pt-BR"
    log.info("→ VivaReal: %s", url)
    results = []
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)

        # Fechar cookie/privacidade banner
        for sel in ["button[id*='cookie']", "button[class*='cookie']", "button[id*='accept']",
                    "#cookie-notifier-cta", "[data-cy='cookie-notifier-cta']"]:
            try:
                await page.click(sel, timeout=2000)
                break
            except Exception:
                pass

        # Scroll para carregar listagens
        for _ in range(6):
            await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
            await page.wait_for_timeout(1200)

        # Busca TODOS os links de imóvel específico
        listing_links = await page.query_selector_all("a[href*='/imovel/']")
        log.info("VivaReal: %d links de imóveis encontrados", len(listing_links))

        seen_hrefs = set()
        for link_el in listing_links[:100]:
            try:
                href = await link_el.get_attribute("href") or ""
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                full_url = f"https://www.vivareal.com.br{href}" if href.startswith("/") else href

                # Subir na árvore DOM até encontrar container do card
                card_text = await link_el.evaluate("""el => {
                    let node = el;
                    for (let i = 0; i < 8; i++) {
                        node = node.parentElement;
                        if (!node) break;
                        const text = node.innerText || '';
                        if (text.includes('R$') && text.length > 50) return text;
                    }
                    return el.closest('section,div,li')?.innerText || '';
                }""")

                # Imagem dentro do container pai
                img_src = await link_el.evaluate("""el => {
                    let node = el;
                    for (let i = 0; i < 8; i++) {
                        node = node.parentElement;
                        if (!node) break;
                        const img = node.querySelector('img[src*="http"]');
                        if (img) return img.src || img.dataset.src || '';
                    }
                    return '';
                }""")

                if "R$" not in card_text or "cascavel" not in card_text.lower():
                    continue

                prop = parse_card_text(card_text, full_url, img_src, "VivaReal")
                if prop:
                    results.append(prop)

            except Exception as e:
                log.debug("Erro link VivaReal: %s", e)

    except Exception as e:
        log.error("VivaReal erro: %s", e)
    finally:
        await page.close()

    # Deduplica por id
    seen = set()
    unique = []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)

    log.info("VivaReal: %d imóveis extraídos", len(unique))
    return unique


# ---------------------------------------------------------------------------
# OLX SCRAPER — filtra por href com regiao-de-cascavel
# ---------------------------------------------------------------------------

async def scrape_olx(ctx) -> list:
    url = "https://www.olx.com.br/imoveis/estado-pr/regiao-de-cascavel/cascavel"
    log.info("→ OLX: %s", url)
    results = []
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(4000)

        # Fechar overlays
        for sel in ["button[id*='accept']", "#onetrust-accept-btn-handler",
                    "button[class*='accept']", "[aria-label='Fechar']"]:
            try:
                await page.click(sel, timeout=2000)
                break
            except Exception:
                pass

        # Scroll
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await page.wait_for_timeout(1000)

        # Todos os links que pertencem a Cascavel
        listing_links = await page.query_selector_all(
            "a[href*='regiao-de-cascavel'][href*='/imoveis/'], "
            "a[href*='cascavel.olx'][href*='/imoveis/']"
        )
        log.info("OLX: %d links de imóveis em Cascavel", len(listing_links))

        seen_hrefs = set()
        for link_el in listing_links[:100]:
            try:
                href = await link_el.get_attribute("href") or ""
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                # Texto do card pai
                card_text = await link_el.evaluate("""el => {
                    let node = el;
                    for (let i = 0; i < 6; i++) {
                        node = node.parentElement;
                        if (!node) break;
                        const text = node.innerText || '';
                        if (text.includes('R$') && text.length > 40) return text;
                    }
                    return '';
                }""")

                img_src = await link_el.evaluate("""el => {
                    let node = el;
                    for (let i = 0; i < 6; i++) {
                        node = node.parentElement;
                        if (!node) break;
                        const img = node.querySelector('img[src*="http"]');
                        if (img) return img.src || '';
                    }
                    return '';
                }""")

                if "R$" not in card_text:
                    # Tenta o texto do link em si
                    card_text = await link_el.inner_text()
                    if "R$" not in card_text:
                        continue

                prop = parse_card_text(card_text, href, img_src, "OLX")
                if prop:
                    results.append(prop)

            except Exception as e:
                log.debug("Erro link OLX: %s", e)

    except Exception as e:
        log.error("OLX erro: %s", e)
    finally:
        await page.close()

    seen = set()
    unique = []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)

    log.info("OLX: %d imóveis extraídos", len(unique))
    return unique


# ---------------------------------------------------------------------------
# ZAPIMOVEIS SCRAPER — busca por links /imovel/
# ---------------------------------------------------------------------------

async def scrape_zap(ctx) -> list:
    url = "https://www.zapimoveis.com.br/venda/imoveis/pr+cascavel/"
    log.info("→ ZapImóveis: %s", url)
    results = []
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)

        for sel in ["#onetrust-accept-btn-handler", "button[class*='accept']",
                    "button[id*='accept']"]:
            try:
                await page.click(sel, timeout=2000)
                break
            except Exception:
                pass

        for _ in range(6):
            await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
            await page.wait_for_timeout(1200)

        listing_links = await page.query_selector_all("a[href*='/imovel/']")
        log.info("ZapImóveis: %d links de imóveis encontrados", len(listing_links))

        seen_hrefs = set()
        for link_el in listing_links[:100]:
            try:
                href = await link_el.get_attribute("href") or ""
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                full_url = f"https://www.zapimoveis.com.br{href}" if href.startswith("/") else href

                card_text = await link_el.evaluate("""el => {
                    let node = el;
                    for (let i = 0; i < 8; i++) {
                        node = node.parentElement;
                        if (!node) break;
                        const text = node.innerText || '';
                        if (text.includes('R$') && text.length > 50) return text;
                    }
                    return el.closest('section,div,li,article')?.innerText || '';
                }""")

                img_src = await link_el.evaluate("""el => {
                    let node = el;
                    for (let i = 0; i < 8; i++) {
                        node = node.parentElement;
                        if (!node) break;
                        const img = node.querySelector('img[src*="http"]');
                        if (img) return img.src || img.dataset.src || '';
                    }
                    return '';
                }""")

                if "R$" not in card_text or "cascavel" not in card_text.lower():
                    continue

                prop = parse_card_text(card_text, full_url, img_src, "ZapImóveis")
                if prop:
                    results.append(prop)

            except Exception as e:
                log.debug("Erro link Zap: %s", e)

    except Exception as e:
        log.error("ZapImóveis erro: %s", e)
    finally:
        await page.close()

    seen = set()
    unique = []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)

    log.info("ZapImóveis: %d imóveis extraídos", len(unique))
    return unique


# ---------------------------------------------------------------------------
# MERGE
# ---------------------------------------------------------------------------

def merge(existing: list, scraped: list) -> tuple:
    existing_ids = {p["id"] for p in existing}
    for p in existing:
        p["is_new"] = False
    result = list(existing)
    new_count = 0
    for item in scraped:
        # Validações adicionais antes de inserir
        if item["id"] in existing_ids:
            continue
        if not titulo_valido(item.get("titulo", "")):
            continue
        if item["preco"] < 50_000 or item["preco"] > MAX_PRECO_PLAUSIVEL:
            continue
        item["is_new"] = True
        result.insert(0, item)
        new_count += 1
        log.info("  ✨ NOVO: %s | R$ %.0f | %s | %s",
                 item["titulo"][:55], item["preco"], item["bairro"], item["fonte"])
    return result, new_count


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

async def main():
    log.info("=" * 60)
    log.info("SCRAPER IMÓVEIS CASCAVEL/PR — v3 Playwright Headless")
    log.info("=" * 60)

    existing = load_existing()
    log.info("Base atual: %d imóveis", len(existing))

    async with async_playwright() as p:
        browser, ctx = await new_context(p)
        try:
            vivareal = await scrape_vivareal(ctx)
            olx      = await scrape_olx(ctx)
            zap      = await scrape_zap(ctx)
        finally:
            await ctx.close()
            await browser.close()

    all_scraped = vivareal + olx + zap
    log.info("Total raspado nos portais: %d", len(all_scraped))

    final, new_count = merge(existing, all_scraped)
    save(final)

    log.info("=" * 60)
    log.info("CONCLUÍDO! Total: %d imóveis | %d NOVOS destacados", len(final), new_count)
    log.info("=" * 60)
    return {"total": len(final), "new": new_count}


if __name__ == "__main__":
    asyncio.run(main())
