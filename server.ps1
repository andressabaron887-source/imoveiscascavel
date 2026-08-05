# Servidor HTTP NATIVO em PowerShell para Imóveis Cascavel/PR
# Funciona em qualquer Windows sem necessidade de Python ou Node.js instalados

$port = 8080
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$port/")
$listener.Prefixes.Add("http://127.0.0.1:$port/")

try {
    $listener.Start()
    Write-Host "=========================================================" -ForegroundColor Green
    Write-Host "  Servidor Imóveis Cascavel/PR Rodando!" -ForegroundColor Cyan
    Write-Host "  Acesse no navegador: http://localhost:$port" -ForegroundColor Yellow
    Write-Host "=========================================================" -ForegroundColor Green
} catch {
    Write-Host "Erro ao iniciar o servidor na porta ${port}: $_" -ForegroundColor Red
    exit 1
}

$baseDir = Get-Location

function Get-ContentType ($path) {
    switch ([System.IO.Path]::GetExtension($path).ToLower()) {
        ".html" { return "text/html; charset=utf-8" }
        ".css"  { return "text/css; charset=utf-8" }
        ".js"   { return "application/javascript; charset=utf-8" }
        ".json" { return "application/json; charset=utf-8" }
        ".png"  { return "image/png" }
        ".jpg"  { return "image/jpeg" }
        default { return "text/plain" }
    }
}

while ($listener.IsListening) {
    try {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        $url = $request.Url.AbsolutePath
        Write-Host "[$($request.HttpMethod)] $url" -ForegroundColor Gray

        if ($url -eq "/api/imoveis" -and $request.HttpMethod -eq "GET") {
            $jsonPath = Join-Path $baseDir "data\imoveis.json"
            $jsonContent = Get-Content -Path $jsonPath -Raw -Encoding UTF8
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($jsonContent)
            $response.ContentType = "application/json; charset=utf-8"
            $response.ContentLength64 = $buffer.Length
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
            $response.Close()
            continue
        }

        if ($url -eq "/api/scrape/trigger" -and $request.HttpMethod -eq "POST") {
            Write-Host "Iniciando raspagem e atualização de imóveis em Cascavel/PR..." -ForegroundColor Yellow
            
            # Chama o script de raspagem nativo
            $scrapeScript = Join-Path $baseDir "scrape.ps1"
            if (Test-Path $scrapeScript) {
                & $scrapeScript
            }

            $jsonPath = Join-Path $baseDir "data\imoveis.json"
            $jsonContent = Get-Content -Path $jsonPath -Raw -Encoding UTF8
            
            $resPayload = @{
                status = "success"
                message = "Raspagem concluída e imóveis atualizados!"
                properties = ($jsonContent | ConvertFrom-Json)
            } | ConvertTo-Json -Depth 10

            $buffer = [System.Text.Encoding]::UTF8.GetBytes($resPayload)
            $response.ContentType = "application/json; charset=utf-8"
            $response.ContentLength64 = $buffer.Length
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
            $response.Close()
            continue
        }

        # Servir Arquivos Estáticos de public/
        if ($url -eq "/") { $url = "/index.html" }
        $filePath = Join-Path $baseDir "public$($url.Replace('/', '\'))"

        if (Test-Path $filePath -PathType Leaf) {
            $buffer = [System.IO.File]::ReadAllBytes($filePath)
            $response.ContentType = Get-ContentType $filePath
            $response.ContentLength64 = $buffer.Length
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
        } else {
            $response.StatusCode = 404
            $errMsg = [System.Text.Encoding]::UTF8.GetBytes("404 - Arquivo não encontrado")
            $response.OutputStream.Write($errMsg, 0, $errMsg.Length)
        }
        $response.Close()

    } catch {
        Write-Host "Erro na requisição: $_" -ForegroundColor Red
    }
}
