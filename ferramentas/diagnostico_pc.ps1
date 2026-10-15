# Diagnostico da Suite Angero: hardware, placa de video e logs do PDF Angero.
# Rodar no PC com problema (botao direito > Executar com o PowerShell).
# Gera "Diagnostico-Suite-<PC>.zip" na Area de Trabalho.
$saida = Join-Path ([Environment]::GetFolderPath('Desktop')) "Diagnostico-Suite-$env:COMPUTERNAME"
New-Item -ItemType Directory -Force $saida | Out-Null

& {
    "PC: $env:COMPUTERNAME  Usuario: $env:USERNAME  Data: $(Get-Date)"
    Get-CimInstance Win32_ComputerSystem | Select-Object Model, @{n='RAM_GB';e={[math]::Round($_.TotalPhysicalMemory/1GB,1)}} | Format-List
    Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | Format-List
    Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, DriverDate, VideoModeDescription | Format-List
    Get-CimInstance Win32_OperatingSystem | Select-Object Caption, BuildNumber, @{n='RAM_livre_GB';e={[math]::Round($_.FreePhysicalMemory/1MB,1)}} | Format-List
    Get-Process | Where-Object { $_.Name -match 'pdf-angero|illustre|fotografe|cena|lightbridge' } | Select-Object Name, Id, CPU, @{n='RAM_MB';e={[math]::Round($_.WorkingSet64/1MB)}}, Responding | Format-Table
} *> (Join-Path $saida 'hardware.txt')

dxdiag /t (Join-Path $saida 'dxdiag.txt') | Out-Null
Start-Sleep -Seconds 2
while (Get-Process dxdiag -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 1 }

foreach ($app in 'PDF-Angero', 'Illustre-Angero', 'Fotografe-Angero', 'Cena-Angero', 'LightBridge-Angero') {
    $logs = Join-Path $env:APPDATA "$app\data\logs"
    if (Test-Path $logs) { Copy-Item $logs (Join-Path $saida $app) -Recurse -Force }
}

Compress-Archive -Path "$saida\*" -DestinationPath "$saida.zip" -Force
Remove-Item $saida -Recurse -Force
Write-Host "Pronto: $saida.zip" -ForegroundColor Green
Start-Sleep -Seconds 5
