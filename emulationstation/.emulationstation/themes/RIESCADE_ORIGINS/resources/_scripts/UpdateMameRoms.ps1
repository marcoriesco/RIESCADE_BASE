param (
    [Parameter(Mandatory=$true, HelpMessage="Caminho do diretório com os arquivos .zip a serem atualizados.")]
    [string]$Directory
)

if (-not (Test-Path -Path $Directory -PathType Container)) {
    Write-Host "Erro: O diretório especificado não existe ($Directory)." -ForegroundColor Red
    exit 1
}

# $BaseUrl = "https://myrient.erista.me/files/MAME/ROMs%20%28non-merged%29/"
$BaseUrl = "https://myrient.erista.me/files/HBMAME/ROMs%20%28merged%29/"
$ZipFiles = Get-ChildItem -Path $Directory -Filter "*.zip" -File

if ($ZipFiles.Count -eq 0) {
    Write-Host "Nenhum arquivo .zip encontrado na pasta $Directory." -ForegroundColor Yellow
    exit 0
}

Write-Host "Encontrado(s) $($ZipFiles.Count) arquivo(s) .zip. Iniciando a atualização..." -ForegroundColor Cyan

foreach ($File in $ZipFiles) {
    $FileName = $File.Name
    # Codifica o nome do arquivo para URL, substituindo espaços e caracteres especiais, exceto quando desnecessário para o nome exato.
    $EncodedName = [uri]::EscapeDataString($FileName)
    $DownloadUrl = $BaseUrl + $EncodedName
    $DestinationPath = $File.FullName
    
    Write-Host "Baixando '$FileName' de Myrient..."
    
    try {
        # Tenta baixar e sobrescrever o arquivo original
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $DestinationPath -UseBasicParsing -ErrorAction Stop
        Write-Host "[OK] Atualizado com sucesso: $FileName" -ForegroundColor Green
    } catch {
        Write-Host "[ERRO] Falha ao baixar $FileName. O arquivo pode não existir no servidor ou houve um erro de rede. Erro: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "Processo de atualização concluído!" -ForegroundColor Cyan
