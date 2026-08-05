$urls = @(
    "https://www.vivareal.com.br/venda/parana/cascavel/",
    "https://www.vivareal.com.br/venda/parana/cascavel/casa_residencial/",
    "https://www.vivareal.com.br/venda/parana/cascavel/apartamento_residencial/",
    "https://www.vivareal.com.br/venda/parana/cascavel/bairros/centro/",
    "https://www.vivareal.com.br/venda/parana/cascavel/bairros/neva/",
    "https://www.vivareal.com.br/venda/parana/cascavel/bairros/coqueiral/",
    "https://www.vivareal.com.br/venda/parana/cascavel/bairros/parque-verde/",
    "https://www.olx.com.br/imoveis/estado-pr/regiao-de-cascavel/cascavel",
    "https://www.imovelweb.com.br/propriedades/venda/cascavel-pr/"
)

foreach ($u in $urls) {
    try {
        $r = Invoke-WebRequest -Uri $u -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -Method Head -ErrorAction SilentlyContinue
        Write-Host "URL: $u -> Status: $($r.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "URL: $u -> Status: $($_.Exception.Message)" -ForegroundColor Red
    }
}
