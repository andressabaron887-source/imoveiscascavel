# -*- coding: utf-8 -*-
"""
Mapeamento de Bairros de Cascavel/PR para Regiões Geográficas
"""

REGION_MAP = {
    # Central
    "Centro": "Central",
    "Neva": "Central",
    "Cancelli": "Central",
    "Parque São Paulo": "Central",
    "Parque Sao Paulo": "Central",
    "Ciro Nardi": "Central",
    "Vila Tolentino": "Central",
    "Country": "Central",
    "Pioneiros Catarinenses": "Central",
    "Vila Industrial": "Central",
    "Jardim Paulista": "Central",
    "Jardim Floresta": "Central",

    # Oeste
    "Coqueiral": "Oeste",
    "Alto Alegre": "Oeste",
    "Santa Cruz": "Oeste",
    "Parque Verde": "Oeste",
    "FAG": "Oeste",
    "Esmeralda": "Oeste",
    "Santos Dumont": "Oeste",
    "Recanto Tropical": "Oeste",
    "Paloma": "Oeste",
    "Aero Clube": "Oeste",
    "São Carlos": "Oeste",
    "Sao Carlos": "Oeste",

    # Leste
    "Região do Lago": "Leste",
    "Regiao do Lago": "Leste",
    "São Cristóvão": "Leste",
    "Sao Cristovao": "Leste",
    "Pacaembu": "Leste",
    "Cataratas": "Leste",
    "Morumbi": "Leste",
    "Periolo": "Leste",
    "Brasília": "Leste",
    "Brasilia": "Leste",

    # Norte
    "Floresta": "Norte",
    "Interlagos": "Norte",
    "Tarumã": "Norte",
    "Taruma": "Norte",
    "Riviera": "Norte",
    "Brasmadeira": "Norte",
    "Alvorada": "Norte",
    "Consolata": "Norte",
    "Jardim Jupira": "Norte",
    "Jardim Bela Vista": "Norte",

    # Sul
    "Cascavel Velho": "Sul",
    "Universitário": "Sul",
    "Universitario": "Sul",
    "14 de Novembro": "Sul",
    "Nova Cidade": "Sul",
    "Santa Felicidade": "Sul",
    "Padre Inácio": "Sul",
    "Padre Inacio": "Sul",
    "Guarujá": "Sul",
    "Guaruja": "Sul",
}


def get_region(bairro: str) -> str:
    """Retorna a região de Cascavel/PR para um bairro dado."""
    if not bairro:
        return "Outros"
    # Exact match first
    if bairro in REGION_MAP:
        return REGION_MAP[bairro]
    # Case-insensitive partial match
    b_lower = bairro.lower().strip()
    for key, region in REGION_MAP.items():
        if key.lower() in b_lower or b_lower in key.lower():
            return region
    return "Outros"
