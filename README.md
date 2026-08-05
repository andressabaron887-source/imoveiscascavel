# 🏢 Imóveis Cascavel/PR — Buscador e Agregador Imobiliário

Buscador e agregador inteligente de imóveis à venda na região de **Cascavel / Paraná**. 
O sistema varre automaticamente os principais portais (**VivaReal, OLX, ZapImóveis**) e **22 imobiliárias locais** de Cascavel/PR.

![Cascavel PR](https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1200&q=80)

---

## 🌟 Funcionalidades

- 📍 **Classificação por Regiões Geográficas:** Central, Oeste, Leste, Norte e Sul de Cascavel/PR.
- 🏢 **Agregação de Portais e Imobiliárias Locais:**
  - VivaReal, OLX, ZapImóveis
  - 22 Imobiliárias Locais (*Porto Seguro, Imobiliária Cidade, Investindo, Providence, LAL, Masterhome, V. Moretti, Presença, Imaginare, Domo, Securitá, Forthe, Seleta, Valencia, HS Cvel, Portal Imóveis, Oeste, Chave de Ouro, Vera Fritz, Brasvalle, Kassol, Elso*).
- 🔗 **Links Oficiais Diretos:** Cada card e modal abre a **página oficial exata do imóvel** no site da imobiliária ou portal correspondente.
- 🔥 **Destaque de Novidades:** Imóveis adicionados na última atualização são sinalizados com a tag `🔥 NOVO!`.
- 🔍 **Filtros Avançados:** Busca por palavra-chave, região, bairro específico, tipo de imóvel, faixa de valor, quantidade mínima de quartos e vagas de garagem.
- 📱 **Design Moderno:** Interface escura, responsiva, com Glassmorphism, animações sutis e ícones Lucide.

---

## 🚀 Como Rodar Localmente (Windows)

1. Clone o repositório:
```bash
git clone https://github.com/SEU_USUARIO/imoveis-cascavel.git
cd imoveis-cascavel
```

2. Execute a configuração inicial (apenas na primeira vez):
```cmd
setup.bat
```

3. Inicie o sistema:
```cmd
start_app.bat
```
O sistema abrirá automaticamente em `http://localhost:8080`.

---

## 🛠️ Tecnologias Utilizadas

- **Frontend:** HTML5, Vanilla CSS3 (Glassmorphism, Flexbox, Grid), JavaScript (ES6+), Lucide Icons
- **Backend:** Python 3.12 (HTTPServer nativo sem dependências pesadas)
- **Scraper / Automação:** Python + Playwright (Chromium Headless)
- **Base de Dados:** JSON estruturado (`data/imoveis.json`)

---

## 📜 Licença
MIT License — Livre para uso e modificação.
