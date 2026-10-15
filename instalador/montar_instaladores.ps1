# Monta os instaladores da Suíte Angerô a partir dos programas compilados nesta máquina.
# Saída padrão: Área de Trabalho\Instaladores Suíte Angerô
#   Instalar Suíte Angerô.exe          (tudo)
#   Instalar <Programa> - Angerô.exe    (avulsos)
# Uso: powershell -ExecutionPolicy Bypass -File montar_instaladores.ps1 [-Versao 1.0.0.0]
param(
    [string]$Versao = "1.0.0.0",
    [string]$Src = "$env:LOCALAPPDATA\SuiteAngero\src",
    [string]$Python = "$env:LOCALAPPDATA\SuiteAngero\build\python",
    [string]$Saida = (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Instaladores Suíte Angerô')
)
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path $PSScriptRoot -Parent
$Build = "$env:LOCALAPPDATA\SuiteAngero\build"
$Iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) { throw "Inno Setup 6 não encontrado (winget install JRSoftware.InnoSetup)" }

$Programas = @(
    @{ Id = 'illustre';    Nome = 'Illustre - Angerô';    Exe = 'illustre';    Icone = 'vetor';   Pasta = 'illustre-angero';    Args = '--control 7979' },
    @{ Id = 'fotografe';   Nome = 'Fotografe - Angerô';   Exe = 'fotografe';   Icone = 'foto';    Pasta = 'fotografe-angero';   Args = '--control 7981 --control-token-file {localappdata}\SuiteAngero\fotografe.token' },
    @{ Id = 'pdf';         Nome = 'PDF - Angerô';         Exe = 'pdf-angero';  Icone = 'pdf';     Pasta = 'pdf-angero';         Args = '' },
    @{ Id = 'cena';        Nome = 'Cena - Angerô';        Exe = 'cena';        Icone = 'video';   Pasta = 'cena-angero';        Args = '--control 7982' },
    @{ Id = 'lightbridge'; Nome = 'LightBridge - Angerô'; Exe = 'lightbridge'; Icone = 'galeria'; Pasta = 'lightbridge-angero'; Args = '--control 7980' }
)

New-Item -ItemType Directory -Force $Saida | Out-Null
$Prog = Join-Path $Build 'programas'
Remove-Item $Prog -Recurse -Force -ErrorAction SilentlyContinue

foreach ($p in $Programas) {
    $rel = Join-Path $Src "$($p.Pasta)\target\release"
    $dest = Join-Path $Prog $p.Id
    New-Item -ItemType Directory -Force $dest | Out-Null
    foreach ($f in "$($p.Exe).exe", "$($p.Exe)-cli.exe") {
        if (-not (Test-Path "$rel\$f")) { throw "$($p.Nome): falta $rel\$f (compile antes: programas\compilar.sh)" }
        Copy-Item "$rel\$f" $dest
    }
    Copy-Item (Join-Path $Src "$($p.Pasta)\LICENSE-APACHE"), (Join-Path $Src "$($p.Pasta)\LICENSE-MIT"), (Join-Path $Src "$($p.Pasta)\NOTICE") $dest
    Set-Content -Path "$dest\versao.txt" -Value $Versao -NoNewline -Encoding ascii
    Write-Host "==> instalador avulso: $($p.Nome)"
    & $Iscc /Q "/DId=$($p.Id)" "/DNome=$($p.Nome)" "/DExe=$($p.Exe)" "/DIcone=$($p.Icone)" "/DArgs=$($p.Args)" `
        "/DVersao=$Versao" "/DFonte=$dest" "/DIcones=$Raiz\icones\ico" "/DSaida=$Saida" "$PSScriptRoot\programa.iss"
    if ($LASTEXITCODE -ne 0) { throw "ISCC falhou: $($p.Nome)" }
}

$arqVersao = Join-Path $Build 'versao-suite.txt'
Set-Content -Path $arqVersao -Value $Versao -NoNewline -Encoding ascii
Write-Host "==> instalador completo: Suíte Angerô"
& $Iscc /Q "/DVersao=$Versao" "/DArqVersao=$arqVersao" "/DRaiz=$Raiz" "/DPython=$Python" "/DProgramas=$Prog" "/DSaida=$Saida" "$PSScriptRoot\suite.iss"
if ($LASTEXITCODE -ne 0) { throw "ISCC falhou: Suíte" }

Get-ChildItem $Saida -Filter *.exe | Select-Object Name, @{n = 'MB'; e = { [math]::Round($_.Length / 1MB, 1) } } | Format-Table -AutoSize
