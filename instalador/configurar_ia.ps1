# Configura a chave do Assistente Angerô (Google Gemini) para TODOS os usuários deste computador.
# O usuário comum não vê nem altera a chave.
# Uso (PowerShell como administrador):  .\configurar_ia.ps1 -Chave "AQ.xxxxx" [-Modelo gemini-3.8-flash]
# Sem administrador, grava em %ProgramData%\SuiteAngero\assistente.json (use quando não puder elevar).
# Por GPO: Preferências › Registro › HKLM\Software\Grupo Angero\Suite Angero\Assistente, valor GeminiChave (REG_SZ).
param(
    [Parameter(Mandatory)] [string]$Chave,
    [string]$Modelo = ""
)
$ErrorActionPreference = 'Stop'
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($admin) {
    $reg = 'HKLM:\Software\Grupo Angero\Suite Angero\Assistente'
    New-Item -Path $reg -Force | Out-Null
    Set-ItemProperty -Path $reg -Name GeminiChave -Value $Chave
    if ($Modelo) { Set-ItemProperty -Path $reg -Name GeminiModelo -Value $Modelo }
    Write-Host "Chave gravada no registro do computador ($reg)."
} else {
    $pasta = Join-Path $env:ProgramData 'SuiteAngero'
    New-Item -ItemType Directory -Force $pasta | Out-Null
    @{ gemini_chave = $Chave; gemini_modelo = $Modelo } | ConvertTo-Json | Set-Content -Path (Join-Path $pasta 'assistente.json') -Encoding utf8
    Write-Host "Sem administrador: chave gravada em $pasta\assistente.json."
}
