#!/bin/bash

# Script to count occurrences of a specific day of the week in a date file

if [ $# -ne 3 ]; then
  echo "Usage: $0 <day_of_week> <input_file> <output_file>"
  echo "  <day_of_week>: Day to count (e.g., Wednesday, Thursday)"
  echo "  <input_file>: Path to the input file containing dates (one per line)"
  echo "  <output_file>: Path to write the count to"
  exit 1
fi

day_of_week_name="$1"
input_file="$2"
output_file="$3"

if ! [ -f "$input_file" ]; then
  echo "Error: Input file '$input_file' not found."
  exit 1
fi

# Convert day of week name to lowercase for case-insensitive matching
day_of_week_lower=$(echo "$day_of_week_name" | tr '[:upper:]' '[:lower:]')

count=0
while IFS= read -r date_str || [ -n "$date_str" ]; do
  day=$(date -d "$date_str" "+%A" | tr '[:upper:]' '[:lower:]') # Get day name, lowercase
  if [ "$day" == "$day_of_week_lower" ]; then
    ((count++))
  fi
done < "$input_file"

echo "$count" > "$output_file"

echo "Counted $count occurrences of $day_of_week_name in '$input_file' and wrote to '$output_file'."