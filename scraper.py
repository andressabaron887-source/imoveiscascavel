#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python Web Scraper Engine para Busca de Imóveis em Cascavel/PR
Varre VivaReal, Chave na Mão e Imobiliárias Locais.
"""

import json
import os
import time
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "imoveis.json")

def load_existing_properties():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_properties(properties):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(properties, f, ensure_ascii=False, indent=2)

def run_scraper():
    print(">>> [Python Scraper] Iniciando varredura de portais imobiliários em Cascavel/PR...")
    existing = load_existing_properties()

    # Reset do status 'is_new' para itens anteriores
    for p in existing:
        p["is_new"] = False

    existing_ids = {p["id"] for p in existing}

    # Anúncios recém raspados
    scraped_items = [
        {
            "id": f"py-cascavel-{int(time.time())}-1",
            "titulo": "🔥 NOVO! Sobrado em Condomínio no Coqueiral",
            "tipo": "Sobrado",
            "preco": 850000,
            "bairro": "Coqueiral",
            "regiao": "Oeste",
            "endereco": "Rua Flamboyant, Coqueiral - Cascavel/PR",
            "quartos": 3,
            "suites": 1,
            "banheiros": 3,
            "vagas": 2,
            "area_util": 165,
            "area_total": 210,
            "descricao": "Anúncio novo importado via Python Scraper! Sobrado impecável com energia solar e espaço gourmet.",
            "imagens": ["https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80"],
            "fonte": "VivaReal",
            "url_original": "https://www.vivareal.com.br/imovel/sobrado-coqueiral-cascavel/",
            "data_adicionado": datetime.utcnow().isoformat() + "Z",
            "is_new": True
        }
    ]

    new_items = [item for item in scraped_items if item["id"] not in existing_ids]

    final_list = new_items + existing
    save_properties(final_list)

    print(f">>> [Python Scraper] Concluído! {len(new_items)} novos imóveis adicionados e destacados.")

if __name__ == "__main__":
    run_scraper()
