$xmlPath = "y:\images\RIESCADE\roms\teknoparrot\gamelist.xml"
$metaDir = "y:\images\RIESCADE\emulators\teknoparrot\Metadata"
$backupPath = "y:\images\RIESCADE\roms\teknoparrot\gamelist.xml.bak"
Copy-Item -Path $xmlPath -Destination $backupPath -Force

[xml]$xml = Get-Content -Path $xmlPath -Raw
$count = 0

foreach ($game in $xml.gameList.game) {
    if (-not $game.name) { continue }
    
    $baseName = $game.name.Trim()
    $jsonPath = Join-Path $metaDir "$baseName.json"
    
    if (Test-Path $jsonPath) {
        try {
            # Write-Host "Processando: $baseName"
            $json = Get-Content $jsonPath -Raw | ConvertFrom-Json
            
            if ($json.game_name -ne $null) {
                # Update the name tag
                $game["name"].InnerText = $json.game_name
            }
            
            # Genre
            if ($json.game_genre -ne $null) {
                if ($game["genre"] -ne $null) {
                    $game["genre"].InnerText = $json.game_genre
                } else {
                    $newElement = $xml.CreateElement("genre")
                    $newElement.InnerText = $json.game_genre
                    $game.AppendChild($newElement) | Out-Null
                }
            }

            # Developer / Publisher
            if ($json.platform -ne $null) {
                if ($game["developer"] -ne $null) {
                    $game["developer"].InnerText = $json.platform
                } else {
                    $newElement = $xml.CreateElement("developer")
                    $newElement.InnerText = $json.platform
                    $game.AppendChild($newElement) | Out-Null
                }
                
                if ($game["publisher"] -ne $null) {
                    $game["publisher"].InnerText = $json.platform
                } else {
                    $newElement = $xml.CreateElement("publisher")
                    $newElement.InnerText = $json.platform
                    $game.AppendChild($newElement) | Out-Null
                }
            }

            # Release Date
            if ($json.release_year -ne $null) {
                $fmDate = "$($json.release_year)0101T000000"
                if ($game["releasedate"] -ne $null) {
                    $game["releasedate"].InnerText = $fmDate
                } else {
                    $newElement = $xml.CreateElement("releasedate")
                    $newElement.InnerText = $fmDate
                    $game.AppendChild($newElement) | Out-Null
                }
            }
            $count++
        } catch {
            Write-Host "Erro em $baseName : $_"
        }
    }
}

Write-Host "Foram atualizados $count jogos."

try {
    # System.Xml.XmlWriterSettings instead to preserve formatting
    $xmlSettings = New-Object System.Xml.XmlWriterSettings
    $xmlSettings.Indent = $true
    $xmlSettings.IndentChars = "`t"
    $xmlSettings.OmitXmlDeclaration = $false

    $writer = [System.Xml.XmlWriter]::Create($xmlPath, $xmlSettings)
    $xml.Save($writer)
    $writer.Close()
    Write-Host "XML Salvo com sucesso!"
} catch {
    Write-Host "Erro ao salvar XML: $_"
}
