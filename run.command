#!/bin/zsh
set -e
cd -- "${0:A:h}"
exec python3 -m ipsc_lab.server --port 8840
