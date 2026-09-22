#!/bin/bash
set -euo pipefail

pnpm install --frozen-lockfile
python -m db.migrate
PORT=4173 BASE_PATH=/ pnpm run build
