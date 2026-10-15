#!/usr/bin/env bash
# Compila os programas da Suíte Angerô (forks do ArtCraft) nesta máquina.
# Uso: bash compilar.sh [illustre fotografe pdf cena lightbridge]   (sem argumentos: todos)
# Requer: Rust (MSVC), Visual Studio Build Tools (C++), e os forks em $SRC.
set -u
SRC="${SRC:-$LOCALAPPDATA/SuiteAngero/src}"
LOG="${LOG:-$LOCALAPPDATA/SuiteAngero/logs}"
mkdir -p "$LOG"
export PATH="$USERPROFILE/.cargo/bin:$PATH"
export CARGO_HTTP_CHECK_REVOKE=false          # proxies corporativos com inspeção HTTPS costumam bloquear a checagem de revogação
export CRAFT_FONTS_DIR="$SRC/craft-fonts"     # fontes embutidas, como nas versões oficiais

declare -A PASTA=( [illustre]=illustre-angero [fotografe]=fotografe-angero [pdf]=pdf-angero [cena]=cena-angero [lightbridge]=lightbridge-angero )
declare -A PACOTE=( [illustre]=vectorcraft [fotografe]=photocraft [pdf]=pdfcraft [cena]=filmcraft [lightbridge]=lightcraft )

alvos=("$@")
[ ${#alvos[@]} -eq 0 ] && alvos=(illustre fotografe pdf cena lightbridge)
for id in "${alvos[@]}"; do
  p=${PACOTE[$id]}
  echo "[$(date +%H:%M:%S)] compilando $id ($p)"
  ( cd "$SRC/${PASTA[$id]}" && cargo build --release --locked -p "$p" -p "$p-cli" ) > "$LOG/build_$id.log" 2>&1
  r=$?
  echo "[$(date +%H:%M:%S)] $id: $([ $r -eq 0 ] && echo OK || echo "FALHOU (veja $LOG/build_$id.log)")"
done
