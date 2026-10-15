# Monta o Python portátil da Suíte (Python "embeddable" oficial + tkinter, usado pelo botão Extensões).
# Uso: preparar_python.ps1 -Instalado <pasta de um Python 3.12 instalado> -Destino <pasta> [-Versao 3.12.10]
param(
    [Parameter(Mandatory)] [string]$Instalado,
    [Parameter(Mandatory)] [string]$Destino,
    [string]$Versao = "3.12.10"
)
$ErrorActionPreference = 'Stop'
Remove-Item $Destino -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $Destino | Out-Null
$zip = Join-Path $env:TEMP "python-$Versao-embed-amd64.zip"
if (-not (Test-Path $zip)) {
    Invoke-WebRequest "https://www.python.org/ftp/python/$Versao/python-$Versao-embed-amd64.zip" -OutFile $zip -UseBasicParsing
}
Expand-Archive $zip -DestinationPath $Destino -Force
# tkinter: módulo, DLLs (Tcl/Tk precisam do zlib1) e bibliotecas Tcl/Tk
Copy-Item "$Instalado\DLLs\_tkinter.pyd", "$Instalado\DLLs\tcl86t.dll", "$Instalado\DLLs\tk86t.dll", "$Instalado\DLLs\zlib1.dll" $Destino
New-Item -ItemType Directory -Force "$Destino\Lib", "$Destino\tcl" | Out-Null
Copy-Item "$Instalado\Lib\tkinter" "$Destino\Lib\" -Recurse
foreach ($d in 'tcl8.6', 'tk8.6', 'tcl8') { Copy-Item "$Instalado\tcl\$d" "$Destino\tcl\" -Recurse }
$mm = ($Versao -split '\.')[0..1] -join ''
Set-Content -Path "$Destino\python$mm._pth" -Value "python$mm.zip`r`n.`r`nLib`r`nLib\site-packages" -Encoding ascii
& "$Destino\python.exe" -c "import tkinter, ssl, winreg; print('python portátil ok', tkinter.TkVersion)"
if ($LASTEXITCODE -ne 0) { throw "python portátil não funcionou" }
