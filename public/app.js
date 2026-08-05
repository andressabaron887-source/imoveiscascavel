// App Client JS - Imóveis Cascavel/PR
// Exibe imóveis de Cascavel com links diretos aos anúncios oficiais e fotos tratadas

let allProperties = [];
let activeRegion = "TODAS";
let activeMinQuartos = 0;
let activeMinVagas = 0;
let isScrapingActive = false;

// Fallback photos por tipo de imóvel (imagens HD reais de alta qualidade)
const TYPE_FALLBACK_IMAGES = {
  "Apartamento": [
    "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1000&q=80"
  ],
  "Casa": [
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1000&q=80"
  ],
  "Sobrado": [
    "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1000&q=80"
  ],
  "Terreno": [
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1000&q=80"
  ],
  "Comercial": [
    "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1000&q=80"
  ]
};

function getValidPropertyImage(item) {
  if (item.imagens && item.imagens.length > 0) {
    const src = item.imagens[0];
    if (src && src.startsWith("http") && !src.endsWith(".svg") && !src.includes("icon") && !src.includes("logo") && !src.includes("avatar")) {
      return src;
    }
  }
  const category = item.tipo || "Apartamento";
  const list = TYPE_FALLBACK_IMAGES[category] || TYPE_FALLBACK_IMAGES["Apartamento"];
  // Seleciona de forma determinística baseado no ID
  const hash = (item.id || "").split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return list[hash % list.length];
}

// Build a real working link to the exact property or portal
function buildPortalURL(item) {
  // SE HOUVER URL ORIGINAL DIRETA DO ANÚNCIO, RETORNA ELA DIRETO!
  if (item && item.url_original && item.url_original.startsWith("http")) {
    return item.url_original;
  }
  const bairro = encodeURIComponent(item.bairro || 'Cascavel');
  return `https://www.vivareal.com.br/venda/parana/cascavel/#onde=,Paran%C3%A1,Cascavel,${bairro},,,,,`;
}

// DOM references
const propertyGrid = document.getElementById("propertyGrid");
const emptyState = document.getElementById("emptyState");
const resultsCountBadge = document.getElementById("resultsCountBadge");
const statTotal = document.getElementById("statTotal");
const statNovos = document.getElementById("statNovos");
const selectBairro = document.getElementById("selectBairro");
const selectTipo = document.getElementById("selectTipo");
const inputKeyword = document.getElementById("inputKeyword");
const inputMinPrice = document.getElementById("inputMinPrice");
const inputMaxPrice = document.getElementById("inputMaxPrice");
const toggleOnlyNew = document.getElementById("toggleOnlyNew");
const selectSort = document.getElementById("selectSort");
const btnScrapeUpdate = document.getElementById("btnScrapeUpdate");
const scrapeProgressBar = document.getElementById("scrapeProgressBar");
const progressFillBar = document.getElementById("progressFillBar");
const progressPercentText = document.getElementById("progressPercentText");
const refreshIcon = document.getElementById("refreshIcon");
const modalBackdrop = document.getElementById("modalBackdrop");
const modalBody = document.getElementById("modalBody");
const btnModalClose = document.getElementById("btnModalClose");

// Init
document.addEventListener("DOMContentLoaded", () => {
  fetchProperties();
  setupEventListeners();
  if (window.lucide) window.lucide.createIcons();
});

async function fetchProperties() {
  try {
    const res = await fetch("/api/imoveis");
    if (res.ok) {
      allProperties = await res.json();
    } else {
      allProperties = await loadFallbackProperties();
    }
  } catch {
    allProperties = await loadFallbackProperties();
  }
  processAndClassifyProperties();
  populateBairroOptions();
  updateStats();
  renderListings();
}

async function loadFallbackProperties() {
  try {
    const res = await fetch("../data/imoveis.json");
    return await res.json();
  } catch { return []; }
}

function processAndClassifyProperties() {
  allProperties.forEach(item => {
    if (!item.regiao || item.regiao === "Outros") {
      item.regiao = getRegionByNeighborhood(item.bairro);
    }
  });
}

function populateBairroOptions() {
  const bairrosSet = new Set();
  allProperties.forEach(item => { if (item.bairro) bairrosSet.add(item.bairro); });
  const sorted = Array.from(bairrosSet).sort();
  selectBairro.innerHTML = `<option value="">Todos os Bairros (${sorted.length})</option>`;
  sorted.forEach(b => {
    const opt = document.createElement("option");
    opt.value = b;
    opt.textContent = `${b} (${getRegionByNeighborhood(b)})`;
    selectBairro.appendChild(opt);
  });
}

function updateStats() {
  statTotal.textContent = allProperties.length;
  const newCount = allProperties.filter(p => p.is_new).length;
  statNovos.textContent = newCount;
  if (newCount > 0) document.getElementById("cardStatNew").classList.add("pulse");
}

function renderListings() {
  const filtered = filterProperties();
  const sorted = sortProperties(filtered);
  resultsCountBadge.textContent = `${sorted.length} de ${allProperties.length}`;
  if (sorted.length === 0) {
    propertyGrid.innerHTML = "";
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");
  propertyGrid.innerHTML = sorted.map(createPropertyCardHTML).join("");
  if (window.lucide) window.lucide.createIcons();
  document.querySelectorAll(".btn-card-details").forEach(btn => {
    btn.addEventListener("click", e => openPropertyModal(e.currentTarget.getAttribute("data-id")));
  });
}

function filterProperties() {
  const keyword = inputKeyword.value.toLowerCase().trim();
  const selectedBairro = selectBairro.value;
  const selectedTipo = selectTipo.value;
  const minPrice = parseFloat(inputMinPrice.value) || 0;
  const maxPrice = parseFloat(inputMaxPrice.value) || Infinity;
  const onlyNew = toggleOnlyNew.checked;
  return allProperties.filter(item => {
    if (activeRegion !== "TODAS" && item.regiao !== activeRegion) return false;
    if (onlyNew && !item.is_new) return false;
    if (selectedBairro && item.bairro !== selectedBairro) return false;
    if (selectedTipo && item.tipo !== selectedTipo) return false;
    if (item.preco < minPrice || item.preco > maxPrice) return false;
    if (activeMinQuartos > 0 && item.quartos < activeMinQuartos) return false;
    if (activeMinVagas > 0 && item.vagas < activeMinVagas) return false;
    if (keyword) {
      const text = `${item.titulo} ${item.bairro} ${item.regiao} ${item.descricao} ${item.tipo} ${item.fonte}`.toLowerCase();
      if (!text.includes(keyword)) return false;
    }
    return true;
  });
}

function sortProperties(list) {
  const mode = selectSort.value;
  return [...list].sort((a, b) => {
    if (mode === "recentes") {
      if (a.is_new !== b.is_new) return b.is_new ? 1 : -1;
      return new Date(b.data_adicionado || 0) - new Date(a.data_adicionado || 0);
    }
    if (mode === "menor_preco") return a.preco - b.preco;
    if (mode === "maior_preco") return b.preco - a.preco;
    if (mode === "area") return (b.area_util || 0) - (a.area_util || 0);
    return 0;
  });
}

function createPropertyCardHTML(item) {
  const formattedPrice = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.preco);
  const mainImage = getValidPropertyImage(item);
  const targetURL = buildPortalURL(item);
  const newBadge = item.is_new
    ? `<span class="badge badge-new-glow"><i data-lucide="sparkles"></i> NOVO!</span>`
    : "";
  const areaDisplay = item.area_util > 0 ? `${item.area_util} m²` : (item.area_total > 0 ? `${item.area_total} m²` : '—');
  const quartosDisplay = item.quartos > 0 ? `${item.quartos} qts` : '— qts';
  const vagasDisplay = item.vagas > 0 ? `${item.vagas} vgs` : '— vgs';

  return `
    <article class="property-card ${item.is_new ? 'is-new-listing' : ''}" id="card-${item.id}">
      <div class="card-image-wrapper">
        ${newBadge}
        <span class="badge badge-region"><i data-lucide="compass"></i> ${item.regiao}</span>
        <span class="badge badge-source" data-fonte="${item.fonte}">${item.fonte}</span>
        <img src="${mainImage}" alt="${item.titulo}" class="card-image" loading="lazy"
          onerror="this.src='https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=800&q=80'">
      </div>
      <div class="card-content">
        <div class="card-price">${formattedPrice}</div>
        <h3 class="card-title">${item.titulo}</h3>
        <div class="card-address"><i data-lucide="map-pin"></i> ${item.bairro} — Cascavel/PR</div>
        <div class="card-specs">
          <div class="spec-item"><i data-lucide="bed"></i> <span>${quartosDisplay}</span></div>
          <div class="spec-item"><i data-lucide="car"></i> <span>${vagasDisplay}</span></div>
          <div class="spec-item"><i data-lucide="maximize-2"></i> <span>${areaDisplay}</span></div>
        </div>
        <div class="card-footer">
          <button class="btn btn-secondary btn-card-details" data-id="${item.id}">
            <i data-lucide="eye"></i> Detalhes
          </button>
          <a href="${targetURL}" target="_blank" rel="noopener noreferrer"
            class="btn-card-link"
            title="Abrir anúncio oficial em ${item.fonte}">
            <i data-lucide="external-link"></i>
          </a>
        </div>
      </div>
    </article>`;
}

function openPropertyModal(id) {
  const item = allProperties.find(p => p.id === id);
  if (!item) return;
  const formattedPrice = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.preco);
  const targetURL = buildPortalURL(item);
  const mainImage = getValidPropertyImage(item);
  const areaDisplay = item.area_util > 0 ? item.area_util : (item.area_total > 0 ? item.area_total : '—');
  const quartosDisplay = item.quartos > 0 ? item.quartos : 'Não informado';
  const vagasDisplay = item.vagas > 0 ? item.vagas : 'Não informado';

  modalBody.innerHTML = `
    <div class="modal-gallery">
      <img src="${mainImage}" alt="${item.titulo}" onerror="this.src='https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=800&q=80'">
    </div>
    <div class="modal-info">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
        <div>
          <span class="badge badge-region" style="position:static; margin-bottom:8px; display:inline-flex;">
            <i data-lucide="compass"></i> Região ${item.regiao}
          </span>
          <h2 style="font-size:1.4rem; color:var(--text-primary);">${item.titulo}</h2>
          <p style="color:var(--text-muted); font-size:0.9rem; margin-top:4px;">
            <i data-lucide="map-pin"></i> ${item.endereco || item.bairro + ' — Cascavel/PR'}
          </p>
        </div>
        <div style="text-align:right;">
          <div style="font-size:1.6rem; font-weight:800; color:var(--accent-cyan);">${formattedPrice}</div>
          <span class="badge badge-source" data-fonte="${item.fonte}"
            style="position:static; display:inline-flex; margin-top:4px;">${item.fonte}</span>
        </div>
      </div>
      <div class="card-specs" style="margin:16px 0; padding:14px; background:rgba(255,255,255,0.03); border-radius:var(--radius-sm);">
        <div class="spec-item"><i data-lucide="bed"></i> <strong>${quartosDisplay}</strong> Quartos${item.suites > 0 ? ` (${item.suites} suíte${item.suites > 1 ? 's' : ''})` : ''}</div>
        <div class="spec-item"><i data-lucide="bath"></i> <strong>${item.banheiros || 1}</strong> Banheiros</div>
        <div class="spec-item"><i data-lucide="car"></i> <strong>${vagasDisplay}</strong> Vagas</div>
        <div class="spec-item"><i data-lucide="maximize-2"></i> <strong>${areaDisplay}</strong> m²</div>
      </div>
      <div style="margin-top:16px;">
        <h4 style="margin-bottom:8px; color:var(--text-secondary);">Descrição do Imóvel:</h4>
        <p style="color:var(--text-secondary); font-size:0.92rem; line-height:1.6;">${item.descricao}</p>
      </div>
      <div style="margin-top:24px;">
        <a href="${targetURL}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="display:flex; gap:8px; align-items:center; justify-content:center; padding:14px;">
          <i data-lucide="external-link"></i>
          Ver Anúncio Oficial no site da ${item.fonte}
        </a>
        <p style="font-size:0.78rem; color:var(--text-muted); text-align:center; margin-top:10px;">
          Link direto: <span style="word-break:break-all; color:var(--accent-cyan);">${targetURL}</span>
        </p>
      </div>
    </div>`;

  modalBackdrop.classList.remove("hidden");
  if (window.lucide) window.lucide.createIcons();
}

function setupEventListeners() {
  document.getElementById("regionPillsContainer").addEventListener("click", e => {
    if (e.target.classList.contains("pill")) {
      document.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
      e.target.classList.add("active");
      activeRegion = e.target.getAttribute("data-region");
      renderListings();
    }
  });

  document.querySelectorAll(".counter-selector").forEach(container => {
    container.addEventListener("click", e => {
      if (e.target.classList.contains("btn-count")) {
        container.querySelectorAll(".btn-count").forEach(b => b.classList.remove("active"));
        e.target.classList.add("active");
        const filterType = container.getAttribute("data-filter");
        const val = parseInt(e.target.getAttribute("data-value"));
        if (filterType === "quartos") activeMinQuartos = val;
        if (filterType === "vagas") activeMinVagas = val;
        renderListings();
      }
    });
  });

  inputKeyword.addEventListener("input", renderListings);
  selectBairro.addEventListener("change", renderListings);
  selectTipo.addEventListener("change", renderListings);
  inputMinPrice.addEventListener("input", renderListings);
  inputMaxPrice.addEventListener("input", renderListings);
  toggleOnlyNew.checked = false;
  toggleOnlyNew.addEventListener("change", renderListings);
  selectSort.addEventListener("change", renderListings);

  document.getElementById("btnResetFilters").addEventListener("click", resetFilters);
  document.getElementById("btnResetFiltersEmpty").addEventListener("click", resetFilters);
  btnScrapeUpdate.addEventListener("click", triggerScrapeUpdate);
  btnModalClose.addEventListener("click", () => modalBackdrop.classList.add("hidden"));
  modalBackdrop.addEventListener("click", e => { if (e.target === modalBackdrop) modalBackdrop.classList.add("hidden"); });
}

function resetFilters() {
  activeRegion = "TODAS";
  activeMinQuartos = 0;
  activeMinVagas = 0;
  document.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
  document.querySelector('.pill[data-region="TODAS"]').classList.add("active");
  document.querySelectorAll(".counter-selector").forEach(c => {
    c.querySelectorAll(".btn-count").forEach(b => b.classList.remove("active"));
    c.querySelector('.btn-count[data-value="0"]').classList.add("active");
  });
  inputKeyword.value = "";
  selectBairro.value = "";
  selectTipo.value = "";
  inputMinPrice.value = "";
  inputMaxPrice.value = "";
  toggleOnlyNew.checked = false;
  renderListings();
}

async function triggerScrapeUpdate() {
  if (isScrapingActive) return;
  isScrapingActive = true;
  btnScrapeUpdate.disabled = true;
  refreshIcon.classList.add("spin");
  scrapeProgressBar.classList.remove("hidden");
  document.getElementById("scrapeStatusText").textContent = "Atualizando Base...";

  let progress = 0;
  const interval = setInterval(() => {
    progress += Math.floor(Math.random() * 12) + 5;
    if (progress > 90) progress = 90;
    progressFillBar.style.width = `${progress}%`;
    progressPercentText.textContent = `${progress}%`;
  }, 300);

  try {
    const res = await fetch("/api/scrape/trigger", { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      if (data.properties) allProperties = data.properties;
    }
  } catch (err) {
    console.warn("Servidor offline, atualização local não disponível.");
  }

  clearInterval(interval);
  progressFillBar.style.width = "100%";
  progressPercentText.textContent = "100%";

  setTimeout(() => {
    scrapeProgressBar.classList.add("hidden");
    refreshIcon.classList.remove("spin");
    btnScrapeUpdate.disabled = false;
    isScrapingActive = false;
    document.getElementById("scrapeStatusText").textContent = "Base Atualizada";
    processAndClassifyProperties();
    populateBairroOptions();
    updateStats();
    toggleOnlyNew.checked = allProperties.some(p => p.is_new);
    renderListings();
  }, 600);
}
