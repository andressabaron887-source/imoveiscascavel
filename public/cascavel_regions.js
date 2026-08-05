// Dicionário completo de Bairros de Cascavel/PR mapeados por Região
const CASCAVEL_REGIONS = {
  "Central": [
    "Centro",
    "Neva",
    "Cancelli",
    "Parque São Paulo",
    "Ciro Nardi",
    "Vila Tolentino",
    "Country",
    "Pioneiros Catarinenses"
  ],
  "Oeste": [
    "Coqueiral",
    "Alto Alegre",
    "Santa Cruz",
    "Parque Verde",
    "FAG",
    "Esmeralda",
    "Santos Dumont",
    "Recanto Tropical",
    "Paloma",
    "Aero Clube"
  ],
  "Leste": [
    "Região do Lago",
    "São Cristóvão",
    "Pacaembu",
    "Cataratas",
    "Morumbi",
    "Periolo",
    "Brasília"
  ],
  "Norte": [
    "Floresta",
    "Interlagos",
    "Tarumã",
    "Riviera",
    "Brasmadeira",
    "Alvorada",
    "Consolata",
    "Jardim Jupira"
  ],
  "Sul": [
    "Cascavel Velho",
    "Universitário",
    "14 de Novembro",
    "Nova Cidade",
    "Santa Felicidade",
    "Padre Inácio",
    "Guarujá"
  ]
};

// Função helper para encontrar a região com base no nome do bairro
function getRegionByNeighborhood(bairroName) {
  if (!bairroName) return "Outros";
  const nameLower = bairroName.toLowerCase().trim();

  for (const [region, bairros] of Object.entries(CASCAVEL_REGIONS)) {
    for (const b of bairros) {
      if (nameLower.includes(b.toLowerCase()) || b.toLowerCase().includes(nameLower)) {
        return region;
      }
    }
  }
  return "Outros";
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { CASCAVEL_REGIONS, getRegionByNeighborhood };
}
