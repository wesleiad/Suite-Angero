# Como editar o visual da Suíte Angerô (sem precisar de IA)

Guia para o TI mexer em cores, textos, ícones e nomes por conta própria.

## 1. Preparar (uma vez)

1. Instale o **VS Code** (`winget install Microsoft.VisualStudioCode`) e, dentro dele, a extensão **rust-analyzer**.
2. Já estão instalados nesta máquina: Rust, Visual Studio Build Tools (C++), Git e o login do `gh`.
   Em outro computador: `winget install Rustlang.Rustup Microsoft.VisualStudio.2022.BuildTools Git.Git GitHub.cli`
   (no Build Tools, marque "Desenvolvimento para desktop com C++").
3. O código de cada programa fica em `%LOCALAPPDATA%\SuiteAngero\src\<programa>-angero`
   (ou baixe com `git clone -b angero https://github.com/wesleiad/<programa>-angero`).

| Programa | Pasta | Pacote (para compilar) |
|---|---|---|
| Illustre | `illustre-angero` | `vectorcraft` |
| Fotografe | `fotografe-angero` | `photocraft` |
| PDF | `pdf-angero` | `pdfcraft` |
| Cena | `cena-angero` | `filmcraft` |
| LightBridge | `lightbridge-angero` | `lightcraft` |

## 2. O que editar

| Quero mudar… | Arquivo (dentro da pasta do programa) | Dica |
|---|---|---|
| **Cores** (fundo, painéis, botões, cor de destaque) | `crates/ui-egui/src/theme.rs` | Procure `accent` e os blocos dos temas claro/escuro. Cores no formato `Color32::from_rgb(0x3F, 0x55, 0xA6)` — esse é o anil da folha Angerô. |
| **Textos em português** (menus, botões, mensagens) | `crates/ui-egui/src/i18n/pt-br.tsv` (LightBridge: `crates/ui-egui/locales/pt-br.json`) | Cada linha: contexto ⇥ texto original ⇥ **tradução**. Mude só a 3ª coluna. |
| **Nome na barra da janela e no Sobre** | procure no VS Code (Ctrl+Shift+F) por `- Angerô` | É um texto entre aspas no código. |
| **Ícone do programa** (janela, barra, .exe) | `assets/app-icon/` | Desenhe/edite em `Suite-Angero/icones/svg/`, rode `python icones/gerar_ico.py` e depois `python programas/rebrand.py <pasta> <id>` para espalhar os ícones. |
| **Página de Ajuda** (menu Ajuda) | `Suite-Angero/docs/ajuda/<id>.md` | Não precisa recompilar: é só editar e dar push. |
| **Iniciador / Assistente** (tela da Suíte) | `Suite-Angero/suite/web/index.html` | Cores no topo do arquivo (`:root { --anil… }`). Não precisa compilar: feche e abra a Suíte. |

Dica: para achar onde um texto aparece, copie o texto da tela e procure no VS Code com **Ctrl+Shift+F**.

## 3. Testar no seu computador

No terminal do VS Code (Ctrl+'), dentro da pasta do programa:

```
$env:CARGO_HTTP_CHECK_REVOKE="false"
cargo run --release -p vectorcraft
```

(troque `vectorcraft` pelo pacote da tabela). A primeira compilação demora; as seguintes só refazem o que mudou.
Para gerar os .exe de todos: `bash Suite-Angero/programas/compilar.sh` (ou só um: `... compilar.sh illustre`).

## 4. Publicar para todos

```
git add -A
git commit -m "visual: nova cor de destaque"
git push
```

- Programas: o push no ramo `angero` faz o GitHub compilar e publicar uma versão nova (aba **Actions** mostra o andamento,
  ~30–60 min). As Suítes instaladas baixam sozinhas.
- Suíte (iniciador, ajuda, ícones): push no `main` do `Suite-Angero` publica a nova versão da Suíte.
- Instaladores para a Área de Trabalho (sem esperar o GitHub): `powershell -File Suite-Angero\instalador\montar_instaladores.ps1`.

## 5. Se der erro

- **Erro de compilação:** o terminal mostra o arquivo e a linha. Desfaça a última mudança (`git checkout -- <arquivo>`) e tente de novo.
- **A Action falhou no GitHub:** abra a aba Actions do repositório, clique na execução vermelha e veja o passo com erro.
- **Voltar uma versão publicada:** `git revert HEAD` e `git push` — sai uma versão nova igual à anterior.
