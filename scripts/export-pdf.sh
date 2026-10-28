#!/bin/sh
# Exports both editions as light-theme PDFs to book/pdf/: sized for the
# reMarkable 2 screen as yokubi-en.pdf and yokubi-zh.pdf, and for phones as
# yokubi-en-phone.pdf and yokubi-zh-phone.pdf.
# Needs mdbook, Google Chrome, and the macOS Hiragino and PingFang fonts.
set -e
cd "$(dirname "$0")/.."
out=book/pdf
chrome=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}

export MDBOOK_OUTPUT__HTML__DEFAULT_THEME=light
export MDBOOK_OUTPUT__HTML__PREFERRED_DARK_THEME=light
export MDBOOK_PREPROCESSOR__FURIGANA__COMMAND="python3 scripts/preprocess-furigana.py"

pdf() {  # pdf <print.html> <the edition's src dir> <PDF> [pdf-postprocess.py options]
  html=$1 src=$2 file=$3
  shift 3
  python3 scripts/pdf-postprocess.py "$html" "$src" "$@"
  "$chrome" --headless --disable-gpu --no-pdf-header-footer --generate-pdf-document-outline \
    --print-to-pdf="$PWD/$file" "file://$PWD/$html"
}

device() {  # device <remarkable|phone> <suffix of its PDFs' names> [pdf-postprocess.py options]
  build=book/$1 suffix=$2
  # The device's page and text sizes are in style/<device>.css.
  export MDBOOK_OUTPUT__HTML__ADDITIONAL_CSS="[\"style/custom.css\", \"style/pdf.css\", \"style/$1.css\"]"
  shift 2
  # The English book is lang="ja"; in the PDF only its tagged Japanese should be.
  # It also has an epub renderer, so its HTML lands in html/.
  MDBOOK_BUILD__BUILD_DIR=$build/en MDBOOK_BOOK__LANGUAGE=en mdbook build
  MDBOOK_BUILD__BUILD_DIR=../$build/zh mdbook build zh
  pdf $build/en/html/print.html src $out/yokubi-en$suffix.pdf "$@"
  pdf $build/zh/print.html zh/src $out/yokubi-zh$suffix.pdf "$@"
}

mkdir -p $out
# The reMarkable draws CJK in the PDF's table of contents as tofu.
device remarkable "" --romaji-toc
device phone -phone
