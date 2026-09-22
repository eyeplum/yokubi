#!/bin/sh
# Builds every language edition into book/html/ (English at the root, Chinese under zh/).
set -e
cd "$(dirname "$0")/.."
mdbook build
mdbook build zh
