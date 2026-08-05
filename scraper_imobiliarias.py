"""
Scraper Completo e Otimizado para as 22 Imobiliárias Locais de Cascavel/PR.
Navega diretamente nas páginas de venda (/venda ou /imoveis/a-venda) e extrai
todos os anúncios diretamente dos sites oficiais de cada imobiliária.
"""
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

AGENCIES = [
    {"name": "Porto Seguro Imóveis", "base": "https://www.portoseguroimobiliaria.com", "search": "https://www.portoseguroimobiliaria.com/venda"},
    {"name": "Imobiliária Cidade", "base": "https://www.imobiliariacidade.com.br", "search": "https://www.imobiliariacidade.com.br/venda"},
    {"name": "Imaginare Imóveis", "base": "https://www.imobimaginare.com.br", "search": "https://www.imobimaginare.com.br/imoveis/a-venda"},
    {"name": "Domo Imóveis", "base": "https://www.imoveisdomo.com.br", "search": "https://www.imoveisdomo.com.br/venda"},
    {"name": "Securitá Imóveis", "base": "https://www.imobiliariasecurita.com.br", "search": "https://www.imobiliariasecurita.com.br/venda"},
    {"name": "Forthe Imobiliária", "base": "https://fortheimobiliaria.com.br", "search": "https://fortheimobiliaria.com.br/venda"},
    {"name": "Imobiliária Seleta", "base": "https://imobiliariaseleta.com.br", "search": "https://imobiliariaseleta.com.br/venda"},
    {"name": "Imobiliária Valencia", "base": "https://www.imobiliariavalencia.com.br", "search": "https://www.imobiliariavalencia.com.br/venda"},
    {"name": "HS Cvel Imóveis", "base": "https://www.hscvelimoveis.com.br", "search": "https://www.hscvelimoveis.com.br/venda"},
    {"name": "Portal Imóveis Cascavel", "base": "https://portalimoveiscascavel.com.br", "search": "https://portalimoveiscascavel.com.br/venda"},
    {"name": "Oeste Imobiliária", "base": "https://www.oesteimobiliaria.com.br", "search": "https://www.oesteimobiliaria.com.br/venda"},
    {"name": "Chave de Ouro Imóveis", "base": "https://chaveouro.com.br", "search": "https://chaveouro.com.br/venda"},
    {"name": "Vera Fritz Imóveis", "base": "https://www.verafritzimobiliaria.com.br", "search": "https://www.verafritzimobiliaria.com.br/venda"},
    {"name": "Investindo Cascavel", "base": "https://www.investindocascavel.com.br", "search": "https://www.investindocascavel.com.br/venda"},
    {"name": "Providence Imóveis", "base": "https://www.imoveisprovidence.com.br", "search": "https://www.imoveisprovidence.com.br/venda"},
    {"name": "Brasvalle Imóveis", "base": "https://imobiliariabrasvalle.com.br", "search": "https://imobiliariabrasvalle.com.br/venda"},
    {"name": "LAL Imóveis", "base": "https://www.imobiliarialal.com.br", "search": "https://www.imobiliarialal.com.br/venda"},
    {"name": "Kassol Imóveis", "base": "https://www.kassolimoveis.com.br", "search": "https://www.kassolimoveis.com.br/venda"},
    {"name": "Masterhome Imobiliária", "base": "https://masterhomeimobiliaria.com.br", "search": "https://masterhomeimobiliaria.com.br/venda"},
    {"name": "Imobiliária V. Moretti", "base": "https://www.imobiliariavmoretti.com.br", "search": "https://www.imobiliariavmoretti.com.br/venda"},
    {"name": "Elso Imóveis", "base": "https://elsoimoveis.com.br", "search": "https://elsoimoveis.com.br/venda"},
    {"name": "Presença Imóveis", "base": "https://www.imoveispresenca.com.br", "search": "https://www.imoveispresenca.com.br/venda"}
]

def make_id(url: str, title: str) -> str:
    raw = f"{url}|{title}"
    return "loc-" + hashlib.md5(raw.encode()).hexdigest()[:12]

def to_float(price_str: str) -> float:
    if not price_str:
        return 0.0
    # Remove R$, espaços e caracteres não numéricos exceto ponto e vírgula
    raw = re.sub(r"[^\d.,]", "", price_str)
    if not raw:
        return 0.0
    # Em pt-BR: se houver vírgula, a parte inteira vem antes da vírgula
    if "," in raw:
        parts = raw.split(",")
        int_part = parts[0].replace(".", "")
        dec_part = parts[1][:2] if len(parts) > 1 else "0"
        val_str = f"{int_part}.{dec_part}"
    else:
        # Se só tiver pontos: se o último ponto tiver 2 ou 3 dígitos depois, trata como milhar ou decimal
        if raw.count(".") > 1:
            val_str = raw.replace(".", "")
        elif raw.count(".") == 1:
            parts = raw.split(".")
            if len(parts[1]) == 2:
                val_str = f"{parts[0]},{parts[1]}".replace(",", ".")
            else:
                val_str = raw.replace(".", "")
        else:
            val_str = raw
    try:
        return float(val_str)
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

def classify(bairro: str) -> str:
    from cascavel_regions_py import get_region
    return get_region(bairro)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

async def scrape_agency(ctx, agency: dict) -> list:
    name = agency["name"]
    base = agency["base"]
    search_url = agency["search"]
    log.info("→ [%s] Acessando página de vendas: %s", name, search_url)
    results = []
    
    page = await ctx.new_page()
    try:
        resp = await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(3000)
        
        # Scroll para acionar carregamento lazy de cards
        for _ in range(4):
            await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
            await page.wait_for_timeout(800)
            
        # Busca links que apontam para detalhe de um imóvel (ex: /imovel/casa-..., /imovel/AP123, etc)
        links = await page.query_selector_all("a[href*='/imovel/'], a[href*='/imovel-'], a[href*='/imoveis/']")
        log.info("[%s] %d links de detalhe encontrados", name, len(links))
        
        seen_urls = set()
        for link in links[:40]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen_urls or href == "/venda" or href.endswith("/imoveis/a-venda"):
                    continue
                seen_urls.add(href)
                
                if href.startswith("/"):
                    full_url = base + href
                elif not href.startswith("http"):
                    full_url = base + "/" + href
                else:
                    full_url = href

                # Sobe na árvore DOM para pegar o texto e imagem do card completo
                card_text = await link.evaluate("""el => {
                    let node = el;
                    for (let i = 0; i < 7; i++) {
                        node = node.parentElement;
                        if (!node) break;
                        const text = node.innerText || '';
                        if (text.includes('R$') && text.length > 20) return text;
                    }
                    return el.innerText || '';
                }""")
                
                img_src = await link.evaluate("""el => {
                    let node = el;
                    for (let i = 0; i < 8; i++) {
                        node = node.parentElement;
                        if (!node) break;
                        const imgs = Array.from(node.querySelectorAll('img'));
                        for (const img of imgs) {
                            const src = img.src || img.dataset.src || img.dataset.original || img.getAttribute('data-lazy') || '';
                            if (src && src.startsWith('http') && !src.includes('.svg') && !src.includes('icon') && !src.includes('logo') && !src.includes('avatar') && !src.includes('favorite')) {
                                return src;
                            }
                        }
                    }
                    return '';
                }""")

                if "R$" not in card_text:
                    continue

                lines = [l.strip() for l in card_text.split("\n") if l.strip()]
                
                # Preço
                preco = 0.0
                for line in lines:
                    if "R$" in line:
                        m = re.search(r"R\$\s*([\d.,]+)", line, re.IGNORECASE)
                        if m:
                            preco = to_float(m.group(1))
                            break

                if preco < 50_000 or preco > 30_000_000:
                    continue

                # Título
                titulo = ""
                for line in lines:
                    if len(line) > 10 and "R$" not in line and not line.startswith("Ref") and not line.startswith("Cód"):
                        titulo = line
                        break
                if not titulo:
                    titulo = f"Imóvel à venda em Cascavel ({name})"

                # Bairro
                bairro = "Centro"
                for line in lines:
                    m = re.search(r"(Centro|Cancelli|Neva|Country|Coqueiral|Parque Verde|FAG|Santa Cruz|Alto Alegre|Esmeralda|Santos Dumont|Região do Lago|São Cristóvão|Pacaembu|Cataratas|Morumbi|Floresta|Interlagos|Tarumã|Riviera|Cascavel Velho|Universitário|14 de Novembro|Guarujá|Santa Felicidade|Recanto Tropical|Brazmadeira|Parque São Paulo|Maria Luiza|Canadá)", line, re.IGNORECASE)
                    if m:
                        bairro = m.group(1).title()
                        break

                quartos = vagas = area = 0
                m = re.search(r"(\d+)\s*(?:quarto|dorm|bed|d\b)", card_text + " " + titulo, re.IGNORECASE)
                if m: quartos = int(m.group(1))
                m = re.search(r"(\d+)\s*(?:vaga|garagem|carro|v\b)", card_text + " " + titulo, re.IGNORECASE)
                if m: vagas = int(m.group(1))
                m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", card_text + " " + titulo, re.IGNORECASE)
                if m: area = to_int(m.group(1).replace(",", ".").split(".")[0])
                if m: vagas = int(m.group(1))
                m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", card_text, re.IGNORECASE)
                if m: area = to_int(m.group(1).replace(",", ".").split(".")[0])

                prop_id = make_id(full_url, titulo)
                
                results.append({
                    "id": prop_id,
                    "titulo": f"{titulo[:80]} — {name}",
                    "tipo": get_tipo(titulo + " " + card_text),
                    "preco": preco,
                    "bairro": bairro,
                    "regiao": classify(bairro),
                    "endereco": f"{bairro}, Cascavel/PR",
                    "quartos": quartos,
                    "suites": 0,
                    "banheiros": max(1, quartos // 2) if quartos > 0 else 1,
                    "vagas": vagas,
                    "area_util": area,
                    "area_total": area,
                    "descricao": f"Anúncio direto de {name} em Cascavel/PR. Confira no site oficial.",
                    "imagens": [img_src] if img_src and img_src.startswith("http") else [],
                    "fonte": name,
                    "url_original": full_url,
                    "data_adicionado": now_iso(),
                    "is_new": False,
                })
            except Exception as e:
                log.debug("Erro card %s: %s", name, e)

    except Exception as e:
        log.warning("[%s] Erro acessando busca: %s", name, e)
    finally:
        await page.close()

    seen = set()
    unique = []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)

    log.info("→ [%s] Extraídos: %d imóveis válidos", name, len(unique))
    return unique

async def main():
    log.info("============================================================")
    log.info("VARREDURA COMPLETA DAS 22 IMOBILIÁRIAS LOCAIS DE CASCAVEL/PR")
    log.info("============================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="pt-BR",
        )

        all_results = []
        for agency in AGENCIES:
            res = await scrape_agency(ctx, agency)
            all_results.extend(res)

        await ctx.close()
        await browser.close()

    log.info("============================================================")
    log.info("TOTAL EXTRAÍDO DAS IMOBILIÁRIAS LOCAIS: %d imóveis", len(all_results))
    log.info("============================================================")

    if DATA_PATH.exists():
        with open(DATA_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    existing_ids = {p["id"] for p in existing}
    new_count = 0
    for p in existing:
        p["is_new"] = False

    for item in all_results:
        if item["id"] not in existing_ids:
            item["is_new"] = True
            existing.insert(0, item)
            new_count += 1
            log.info("  ✨ NOVO (%s): %s | R$ %.0f | %s", item["fonte"], item["titulo"][:45], item["preco"], item["bairro"])

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    log.info("Base final atualizada: %d imóveis (%d novos marcados)", len(existing), new_count)

if __name__ == "__main__":
    asyncio.run(main())
