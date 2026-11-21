#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
. ~/.config/screenhawk/openai.env
set +a
exec python3 -u -m experiment.run --live "$@"
