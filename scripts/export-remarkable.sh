#!/bin/sh
# Exports both editions as light-theme PDFs sized for the reMarkable 2 screen,
# written to book/remarkable/yokubi-en.pdf and yokubi-zh.pdf.
# Needs mdbook, Google Chrome, and the macOS Hiragino and PingFang fonts.
set -e
cd "$(dirname "$0")/.."
out=book/remarkable
chrome=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}

export MDBOOK_OUTPUT__HTML__DEFAULT_THEME=light
export MDBOOK_OUTPUT__HTML__PREFERRED_DARK_THEME=light
export MDBOOK_OUTPUT__HTML__ADDITIONAL_CSS='["style/custom.css", "style/remarkable.css"]'
export MDBOOK_PREPROCESSOR__FURIGANA__COMMAND="python3 scripts/preprocess-furigana.py"

# The English book is lang="ja"; in the PDF only its tagged Japanese should be.
# It also has an epub renderer, so its HTML lands in html/.
MDBOOK_BUILD__BUILD_DIR=$out/en MDBOOK_BOOK__LANGUAGE=en mdbook build
MDBOOK_BUILD__BUILD_DIR=../$out/zh mdbook build zh

pdf() {  # pdf <edition> <print.html> <the edition's src dir>
  python3 scripts/remarkable-postprocess.py "$2" "$3"
  "$chrome" --headless --disable-gpu --no-pdf-header-footer --generate-pdf-document-outline \
    --print-to-pdf="$PWD/$out/yokubi-$1.pdf" "file://$PWD/$2"
}
pdf en $out/en/html/print.html src
pdf zh $out/zh/print.html zh/src
