#!/bin/bash

# Activate the virtual environment
source /app/venv/bin/activate

# Script to sort a JSON array of contacts by specified keys with ascending/descending order

if [ $# -lt 4 ]; then
  echo "Usage: $0 <input_file> <output_file> <order> <sort_key1> [sort_key2 ...]"
  echo "  <input_file>: Path to the input JSON file (within /data)."
  echo "  <output_file>: Path to write the sorted JSON array (within /data)."
  echo "  <order>: Sorting order, either 'asc' for ascending or 'desc' for descending."
  echo "  <sort_key1> [sort_key2 ...]: One or more keys to sort by."
  exit 1
fi

input_file="$1"
output_file="$2"
sort_order="$3" # New sort order argument
shift # Remove input_file
shift # Remove output_file
shift # Remove sort_order
sort_keys=("$@") # Remaining arguments are sort keys

if ! [ -f "$input_file" ]; then
  echo "Error: Input file '$input_file' not found."
  exit 1
fi

if [ ${#sort_keys[@]} -eq 0 ]; then
  echo "Error: At least one sort key must be provided."
  echo "Usage: $0 <input_file> <output_file> <order> <sort_key1> [sort_key2 ...]"
  exit 1
fi

# Validate sort_order
if [[ "$sort_order" != "asc" && "$sort_order" != "desc" ]]; then
  echo "Error: Invalid sort order. Must be 'asc' or 'desc'."
  echo "Usage: $0 <input_file> <output_file> <order> <sort_key1> [sort_key2 ...]"
  exit 1
fi

# Embedded Python to perform JSON sorting
python_code=$(cat <<END_PYTHON
import json
import sys

input_filepath = sys.argv[1]
output_filepath = sys.argv[2]
sort_order = sys.argv[3] # Get sort order from command line
sort_keys = sys.argv[4:]

try:
    with open(input_filepath, 'r') as infile:
        contacts = json.load(infile)
except FileNotFoundError:
    print(f"Error: Input file not found: {input_filepath}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Invalid JSON in input file: {input_filepath}")
    sys.exit(1)

if not isinstance(contacts, list):
    print(f"Error: Input file does not contain a JSON array: {input_filepath}")
    sys.exit(1)

def sort_function(contact):
    return tuple(contact.get(key, "") for key in sort_keys)[::-1]

reverse_sort = (sort_order == 'desc') # Determine reverse based on sort_order

sorted_contacts = sorted(contacts, key=sort_function, reverse=reverse_sort) # Apply reverse sort

try:
    with open(output_filepath, 'w') as outfile:
        json.dump(sorted_contacts, outfile, indent=2)
except Exception as e:
    print(f"Error writing to output file: {output_filepath} - {e}")
    sys.exit(1)

print(f"Sorted contacts from '{input_filepath}' by keys {sort_keys} in {sort_order} order and wrote to '{output_filepath}'.")

END_PYTHON
)

uv run python -c "$python_code" "$input_file" "$output_file" "$sort_order" "${sort_keys[@]}"

if [ $? -eq 0 ]; then
  echo "Successfully sorted contacts from '$input_file' and wrote to '$output_file'."
else
  echo "Error sorting contacts from '$input_file'."
  exit 1
fi