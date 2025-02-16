#!/bin/bash

# Activate the virtual environment
source /app/venv/bin/activate

# Script to run datagen.py to generate data files in /data directory.
# Usage: a1.sh <email_address>

if [ $# -ne 1 ]; then
  echo "Usage: $0 <email_address>"
  echo "  <email_address>: Email address to be used with datagen.py"
  exit 1
fi

email_address="$1"

uv run https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py --root /data/ "$email_address"