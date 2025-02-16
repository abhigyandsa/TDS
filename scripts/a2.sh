#!/bin/bash

# Script to format a Markdown file using npx prettier with a specified version

source venv/bin/activate

if [ $# -ne 2 ]; then
  echo "Usage: $0 <markdown_file_path> <prettier_version>"
  echo "  <markdown_file_path>: Path to the Markdown file to format (within /data)"
  echo "  <prettier_version>: Version of prettier to use (e.g., 3.4.2)"
  exit 1
fi

markdown_file_path="$1"
prettier_version="$2"

if ! [ -f "$markdown_file_path" ]; then
  echo "Error: Markdown file $markdown_file_path not found."
  exit 1
fi

# Security: Explicitly invoke only 'prettier' via npx and specify version
command="npx -y prettier@${prettier_version} --write $markdown_file_path"

echo "Executing command: $command" # Optional: For debugging
echo

eval "$command" # Execute the prettier command

if [ $? -eq 0 ]; then
  echo "Successfully formatted $markdown_file_path using prettier@${prettier_version}."
else
  echo "Error formatting $markdown_file_path using prettier@${prettier_version}."
  exit 1
fi