$req = Invoke-WebRequest -Uri "https://www.imovelweb.com.br/propriedades/venda/cascavel-pr/" -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -ErrorAction SilentlyContinue
Write-Host "Status Imovelweb: $($req.StatusCode)"
Write-Host "Content Length: $($req.Content.Length)"
