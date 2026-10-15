# Suíte Angerô

Pacote gratuito de programas de criação do **Grupo Angerô**, com identidade visual da empresa,
**Assistente de IA** integrado e atualização automática.

| Programa | Para quê | Ajuda |
|---|---|---|
| **Illustre - Angerô** | Desenho vetorial: fichas técnicas, estampas, artes (padrão Illustrator) | [docs/ajuda/illustre.md](docs/ajuda/illustre.md) |
| **Fotografe - Angerô** | Edição de imagens com camadas, abre PSD (padrão Photoshop) | [docs/ajuda/fotografe.md](docs/ajuda/fotografe.md) |
| **PDF - Angerô** | Ler, juntar, organizar, assinar e proteger PDFs | [docs/ajuda/pdf.md](docs/ajuda/pdf.md) |
| **Cena - Angerô** | Edição de vídeo (padrão Premiere) | [docs/ajuda/cena.md](docs/ajuda/cena.md) |
| **LightBridge - Angerô** | Catálogo, revelação e exportação de fotos | [docs/ajuda/lightbridge.md](docs/ajuda/lightbridge.md) |
| **Suíte Angerô** | Iniciador, busca de arquivos, Assistente de IA, extensões | [docs/ajuda/suite.md](docs/ajuda/suite.md) |

## Instalar

Baixe na aba **Releases** deste repositório:

- **Instalar Suíte Angerô** — tudo: iniciador, assistente e os 5 programas;
- ou o instalador **avulso** de cada programa, na aba Releases do repositório de cada um.

Os instaladores não pedem senha de administrador (instalam por usuário). Depois de instalada, a Suíte confere
o GitHub ao abrir e a cada 6 horas e **se atualiza sozinha** (programas fechados são atualizados na hora;
os abertos, quando forem fechados).

## Como as atualizações chegam

1. Alteração no código → `git push`.
2. O GitHub Actions compila e publica uma versão nova em **Releases** (`versao.txt` + pacote `.zip` + instalador).
3. As Suítes instaladas baixam a versão nova sozinhas.

| Repositório | Conteúdo |
|---|---|
| [Suite-Angero](https://github.com/wesleiad/Suite-Angero) | iniciador, assistente, ícones, instaladores, ajuda |
| [illustre-angero](https://github.com/wesleiad/illustre-angero) | Illustre - Angerô |
| [fotografe-angero](https://github.com/wesleiad/fotografe-angero) | Fotografe - Angerô |
| [pdf-angero](https://github.com/wesleiad/pdf-angero) | PDF - Angerô |
| [cena-angero](https://github.com/wesleiad/cena-angero) | Cena - Angerô |
| [lightbridge-angero](https://github.com/wesleiad/lightbridge-angero) | LightBridge - Angerô |

## Estrutura

```
suite/        iniciador (servidor local 127.0.0.1:8790), Assistente de IA (Google Gemini), busca de arquivos,
              ponte com os programas (MCP), extensões no estilo CEP (porta 8792), atualizador
icones/       ícones da Suíte (gerar_svg.py desenha, gerar_ico.py gera PNG/ICO)
instalador/   instaladores Inno Setup (Suíte completa e avulsos) e montar_instaladores.ps1
programas/    rebrand.py, limpar_fork.py e compilar.sh — aplicam a identidade Angerô nos programas
docs/ajuda/   páginas de Ajuda abertas pelos menus Ajuda dos programas
plugins/      extensões instaladas localmente (não versionadas)
```

Assistente de IA: plano gratuito do Google Gemini; a chave fica só no computador do usuário
(`%APPDATA%\SuiteAngero\config.json`). No plano gratuito o Google pode usar o que é digitado no chat —
não envie informações sigilosas pelo assistente.

## Código-base e licença

Desenvolvido por **Weslei Domingues (TI)** para o Grupo Angerô.
Os cinco programas foram construídos a partir do código aberto do projeto **ArtCraft**
(VectorCraft, PhotoCraft, PdfCraft, FilmCraft e LightCraft — https://github.com/storytold), usado como base,
sob licença MIT OU Apache-2.0; os avisos de licença originais estão em cada repositório.
O código deste repositório está sob a licença MIT (arquivo `LICENSE`).
