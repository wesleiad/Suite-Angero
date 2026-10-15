# Programas padrão para cada tipo de arquivo

Os instaladores têm a opção **"Usar como programa padrão"** (marcada). Ela registra cada programa para as extensões dele:

| Programa | Vira o padrão de | Só aparece em "Abrir com" |
|---|---|---|
| Illustre | .ai .ait .eps .svg .svgz | .pdf .dxf .emf .wmf |
| Fotografe | .psd .psb | .png .jpg .jpeg .tif .tiff .webp .bmp .gif .tga |
| PDF | .pdf | — |
| Cena | projeto do Cena | .mp4 .mov .mkv .avi e áudios |
| LightBridge | RAW (.cr2 .cr3 .nef .arw .dng .raf .orf .rw2) | .jpg .jpeg .png .tif .tiff |

Limite do Windows 10/11: se o usuário já tinha escolhido "sempre abrir com" outro programa para uma extensão,
o Windows mantém a escolha dele. Para **forçar em todos os computadores do domínio**:

1. Copie `docs/ti/AssociacoesPadrao.xml` para um compartilhamento que todos leem (ex.: `\\servidor\NETLOGON\SuiteAngero\`).
2. GPO › Configuração do Computador › Modelos Administrativos › Componentes do Windows › Explorador de Arquivos ›
   **Definir um arquivo de configuração de associações padrão** › Habilitado › caminho do XML.
3. Vale no próximo logon (a Suíte precisa estar instalada para os programas existirem).

O XML é gerado por `instalador/gerar_associacoes.py` (mesma lista dos instaladores).
