$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Sobe 4 niveis a partir de _scripts ate chegar em .emulationstation
$EsSystemsDir = (Get-Item (Join-Path $ScriptDir "..\..\..\..")).FullName

$EsSystemsPath = Join-Path $EsSystemsDir "es_systems.cfg"
$ArtsPath = Join-Path $EsSystemsDir "themes\RIESCADE_ORIGINS\resources\arts"
$LogosPath = Join-Path $EsSystemsDir "themes\RIESCADE_ORIGINS\resources\logos"

$MissingArts = [System.Collections.Generic.List[string]]::new()
$MissingLogos = [System.Collections.Generic.List[string]]::new()

[xml]$EsSystems = Get-Content -Path $EsSystemsPath -Raw
$SystemNodes = $EsSystems.systemList.system

foreach ($Node in $SystemNodes) {
    $SystemName = $Node.name
    if ([string]::IsNullOrWhiteSpace($SystemName)) { continue }
    $SystemName = $SystemName.Trim()
    
    # Check Arts
    $ArtFiles = Get-ChildItem -Path $ArtsPath -Filter "$SystemName.*" -File -ErrorAction SilentlyContinue
    if (-not $ArtFiles) {
        $MissingArts.Add($SystemName)
    }
    
    # Check Logos
    $LogoFiles = Get-ChildItem -Path $LogosPath -Filter "$SystemName.*" -File -ErrorAction SilentlyContinue
    if (-not $LogoFiles) {
        $MissingLogos.Add($SystemName)
    }
}

Write-Output "========== MISSING ARTS ($($MissingArts.Count)) =========="
$MissingArts -join ", " | Write-Output

Write-Output ""
Write-Output "========== MISSING LOGOS ($($MissingLogos.Count)) =========="
$MissingLogos -join ", " | Write-Output
