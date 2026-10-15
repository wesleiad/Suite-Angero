@echo off
rem Abre o PDF Angero desenhando a tela com OpenGL em vez de DirectX 12.
rem Se assim nao travar, o problema e a placa de video/driver do PC.
set PDFCRAFT_RENDERER=gl
set WGPU_BACKEND=gl
for /d %%D in ("%LOCALAPPDATA%\Programs\Suite Angero\PDF - Anger*") do start "" "%%D\pdf-angero.exe" %*
