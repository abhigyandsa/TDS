#!/bin/bash

# Activate the virtual environment
source /app/venv/bin/activate

# Script to create an index of Markdown files in a directory, mapping filename to first H1 header.

if [ $# -ne 2 ]; then
  echo "Usage: $0 <markdown_dir> <output_dir>"
  echo "  <markdown_dir>: Directory to search for Markdown files (within /data/docs/)"
  echo "  <output_dir>: Directory to write the index.json file to (within /data/docs/)"
  exit 1
fi

markdown_dir="$1"
output_dir="$2"

if ! [ -d "$markdown_dir" ]; then
  echo "Error: Markdown directory '$markdown_dir' not found."
  exit 1
fi

if ! [ -d "$output_dir" ]; then
  echo "Error: Output directory '$output_dir' not found."
  exit 1
fi

index_file="${output_dir}/index.json"

index_data="{" # Start JSON object

file_count=0
find "$markdown_dir" -name "*.md" -type f 2>/dev/null | tee /dev/stderr | while IFS= read -r markdown_file; do  filename_relative=$(basename "$markdown_file") # Get filename relative to markdown_dir
  title=$(grep "^# " "$markdown_file" | head -n 1 | sed 's/^# //') # Extract first H1

  if [[ -n "$title" ]]; then # If title is found
    if [ $file_count -gt 0 ]; then
      index_data+="," # Add comma if not the first entry
    fi
    index_data+="\n  \"${filename_relative}\": \"$(jq -sRr @json <<<"$title")\"" # Add filename: title pair, escape title for JSON
    ((file_count++))
  fi
done

index_data+="\n}" # End JSON object

echo "$index_data" > "$index_file"

echo "Created index file '$index_file' with $file_count entries."