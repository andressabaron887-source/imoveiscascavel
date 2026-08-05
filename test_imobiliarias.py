"""
Script para testar a estrutura e acessibilidade das 22 imobiliárias de Cascavel/PR
"""
import asyncio
import json
from playwright.async_api import async_playwright
from pathlib import Path

URLS = [
    "https://fortheimobiliaria.com.br/",
    "https://www.portoseguroimobiliaria.com/",
    "https://www.imobiliariacidade.com.br/",
    "https://imobiliariaseleta.com.br/",
    "https://www.imobiliariavalencia.com.br/",
    "https://www.hscvelimoveis.com.br/",
    "https://portalimoveiscascavel.com.br/",
    "https://www.oesteimobiliaria.com.br/",
    "https://chaveouro.com.br/",
    "https://www.verafritzimobiliaria.com.br/",
    "https://www.investindocascavel.com.br/",
    "https://www.imoveisprovidence.com.br/",
    "https://imobiliariabrasvalle.com.br/",
    "https://www.imobiliarialal.com.br/",
    "https://www.kassolimoveis.com.br/inicio",
    "https://masterhomeimobiliaria.com.br/",
    "https://www.imobiliariavmoretti.com.br/",
    "https://www.imobimaginare.com.br/",
    "https://elsoimoveis.com.br/",
    "https://www.imoveispresenca.com.br/",
    "https://www.imoveisdomo.com.br/",
    "https://www.imobiliariasecurita.com.br/"
]

async def check_sites():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="pt-BR"
        )
        
        results = []
        for url in URLS:
            page = await ctx.new_page()
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(2000)
                title = await page.title()
                status = resp.status if resp else 0
                
                # Procurar links de venda ou busca
                links = await page.query_selector_all("a[href]")
                venda_links = []
                for link in links:
                    href = await link.get_attribute("href") or ""
                    text = (await link.inner_text()).lower()
                    if "comprar" in text or "venda" in text or "comprar" in href or "venda" in href:
                        venda_links.append(href)
                
                print(f"[{status}] {url} -> Title: {title[:40]} | Links venda: {len(venda_links)}")
                results.append({
                    "url": url,
                    "status": status,
                    "title": title,
                    "venda_links": venda_links[:5]
                })
            except Exception as e:
                print(f"[ERR] {url} -> {e}")
                results.append({"url": url, "error": str(e)})
            finally:
                await page.close()
                
        await browser.close()
        
    with open("imobiliarias_test.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(check_sites())
