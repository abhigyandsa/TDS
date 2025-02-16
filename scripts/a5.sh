#!/bin/bash

# Activate the virtual environment
source /app/venv/bin/activate

# Script to write the first line of the N most recent files with a given extension
# from a directory to an output file.

if [ $# -ne 5 ]; then
  echo "Usage: $0 <extension> <containing_dir> <output_dir> <n_recent> <m_lines>"
  echo "  <extension>: File extension to filter for (e.g., .log)"
  echo "  <containing_dir>: Directory to search for files (within /data)"
  echo "  <output_dir>: Directory to write the output file to (within /data)"
  echo "  <n_recent>: Number of most recent files to consider (integer)"
  echo "  <m_lines>: Number of lines to extract from each file (integer, typically 1)"
  exit 1
fi

extension="$1"
containing_dir="$2"
output_dir="$3"
n_recent="$4"
m_lines="$5"

if ! [ -d "$containing_dir" ]; then
  echo "Error: Containing directory '$containing_dir' not found."
  exit 1
fi

if ! [ -d "$output_dir" ]; then
  echo "Error: Output directory '$output_dir' not found."
  exit 1
fi

if ! [[ "$n_recent" =~ ^[0-9]+$ ]]; then
  echo "Error: n_recent '$n_recent' is not a positive integer."
  exit 1
fi
n_recent_int=$(printf "%d" "$n_recent") # Ensure integer

if ! [[ "$m_lines" =~ ^[0-9]+$ ]]; then
  echo "Error: m_lines '$m_lines' is not a positive integer."
  exit 1
fi
m_lines_int=$(printf "%d" "$m_lines") # Ensure integer


output_file="${output_dir}/logs-recent.txt" # Fixed output file name

# Find files, sort by modification time (descending), limit to n_recent
recent_files=$(find "$containing_dir" -name "*.$extension" -type f 2>/dev/null |
                while IFS= read -r file; do
                    stat -c "%Y %n" "$file"
                done |
                sort -rn | # sort -r (reverse) -n (numeric)
                head -n "$n_recent_int" |
                awk '{print $2}') # Extract only the file paths


if [[ -z "$recent_files" ]]; then
  echo "No files with extension '$extension' found in '$containing_dir'."
  echo "" > "$output_file" # Create empty output file
  exit 0 # Not an error, just no files found
fi


# Process each recent file and extract the first m_lines
echo "" > "$output_file" # Clear output file
file_count=0
while IFS= read -r recent_file; do
  if [ $file_count -lt "$n_recent_int" ]; then
    head -n "$m_lines_int" "$recent_file" | head -n 1 >> "$output_file" # Get first line, append to output
    ((file_count++))
  fi
done < <(echo "$recent_files")


echo "Wrote first line from $file_count most recent '.$extension' log files from '$containing_dir' to '$output_file'."