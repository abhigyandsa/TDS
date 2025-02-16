import requests
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import subprocess

load_dotenv()

app = Flask(__name__)

DATA_DIR = "/data"  # Define the base /data directory inside the container

AIPROXY_URL = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")  # Load token from environment
LLM_MODEL_NAME = "gpt-4o-mini"


def call_llm(prompt):
    system_prompt = """
    You are a helpful automation agent. You can generate bash commands to execute specific tasks.
    You have access to a set of pre-written bash scripts located in the /app/scripts directory.

    Here is a description of the available scripts and how to use them:

    **Script: a1.sh**
    Description: Installs 'uv' (if required) and runs the 'datagen.py' script to generate data files in the /data directory. It now requires an email address as an argument.
    Usage: /app/scripts/a1.sh <email_address>
    - <email_address>: Email address to be used with datagen.py. Example: your_email@example.com


    **Script: a2.sh**
    Description: Formats a Markdown file in-place using npx prettier.
    Usage: /app/scripts/a2.sh <markdown_file_path> <prettier_version>
    - <markdown_file_path>: Path to the Markdown file to format (within /data directory). Example: /data/format.md
    - <prettier_version>: Version of prettier to use. Example: 3.4.2

    **Script: a3.sh**
    Description: Counts the number of occurrences of a specific day of the week in a file containing dates (one date per line).
    Usage: /app/scripts/a3.sh <day_of_week> <input_file> <output_file>
    - <day_of_week>: The day of the week to count (e.g., Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday). Case-insensitive. Should provide the day in English only. Translate if required.
    - <input_file>:  Path to the input file within the /data directory.
    - <output_file>: Path to the output file within the /data directory where the count will be written.

    **Script: a4.sh**
    Description: Sorts a JSON array of contact objects with specified sort order and keys.
    Usage: /app/scripts/a4.sh <input_file> <output_file> <order> <sort_key1> [sort_key2 ...]
    - <input_file>: Path to the input JSON file (within /data). Example: /data/contacts.json
    - <output_file>: Path to write the sorted JSON array to (within /data). Example: /data/contacts-sorted.json
    - <order>: Sorting order, either 'asc' for ascending or 'desc' for descending. Example: asc or desc
    - <sort_key1> [sort_key2 ...]: One or more keys to sort by, in reverse of priority. That is last key is the primary sort key.

    **Script: a5.sh**
    Description: Writes the first line of the N most recent files with a given extension from a directory to an output file.
    Usage: /app/scripts/a5.sh <extension> <containing_dir> <output_dir> <n_recent> <m_lines>
    - <extension>: File extension to filter for (e.g., log). Example: log
    - <containing_dir>: Directory to search for files in (within /data). Example: /data/logs
    - <output_dir>: Directory to write the output file to (within /data). Example: /data
    - <n_recent>: Number of most recent files to consider (integer). Example: 10
    - <m_lines>: Number of lines to extract from each file (integer). Example: 1

    **Script: a6.sh**
    Description: Creates an index file (index.json) mapping Markdown filenames to their first H1 headers.
    Usage: /app/scripts/a6.sh <markdown_dir> <output_dir>
    - <markdown_dir>: Directory to search for Markdown files (within /data/docs/). Example: /data/docs
    - <output_dir>: Directory to write the index.json file to (within /data/docs/). Example: /data/docs



    **Constraints:**

    - All input and output files MUST be within the /data directory.
    - You MUST generate a single bash command line to execute the script with the correct arguments (if any).
    - Do not generate any explanatory text before or after the command. Only output the raw bash command.
    - Assume the scripts are already executable in the /app/scripts directory.

    Example Task for a3.sh: "Count the number of Fridays in /data/dates.txt and write the count to /data/friday_counts.txt"
    Example Command for a3.sh: /app/scripts/a3.sh Friday /data/dates.txt /data/friday_counts.txt

    Example Task for a2.sh: "Format document.md using prettier version 3.4.2"
    Example Command for a2.sh: /app/scripts/a2.sh /data/document.md 3.4.2

    Example Task for a1.sh: "Generate data files using email 21f1003422@ds.study.iitm.ac.in"
    Example Command for a1.sh: /app/scripts/a1.sh 21f1003422@ds.study.iitm.ac.in


    Example Task for a4.sh (ascending): "Sort contacts in /data/contacts.json in ascending order by last_name then first_name and save to /data/contacts-sorted-asc.json"
    Example Command for a4.sh (ascending): /app/scripts/a4.sh /data/contacts.json /data/contacts-sorted-asc.json asc last_name first_name

    Example Task for a4.sh (descending): "Sort contacts in /data/contacts.json in descending order by first_name then last_name and save to /data/contacts-sorted-desc.json"
    Example Command for a4.sh (descending): /app/scripts/a4.sh /data/contacts.json /data/contacts-sorted-desc.json desc first_name last_name


    Example Task for a5.sh: "Write first line of 5 most recent .log files from /data/logs to /data/logs-recent.txt"
    Example Command for a5.sh: /app/scripts/a5.sh log /data/logs /data 5 1

    Example Task for a6.sh: "Create markdown index of docs directory in /data/docs/index.json"
    Example Command for a6.sh: /app/scripts/a6.sh /data/docs /data/docs

    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
    }
    data = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        response = requests.post(AIPROXY_URL, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        response_json = response.json()
        llm_response_content = (
            response_json.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        return llm_response_content
    except requests.exceptions.Timeout:
        return "LLM API request timed out."
    except requests.exceptions.RequestException as e:
        return f"Error calling LLM API: {e}"
    except Exception as e:
        return f"Unexpected error processing LLM response: {e}"


@app.route("/run", methods=["POST"])
def run_task():
    task_description = request.args.get("task")
    if task_description:
        user_prompt = task_description.strip()

        llm_command_response = call_llm(user_prompt)

        if (
            llm_command_response.startswith("Error calling LLM API")
            or llm_command_response == "LLM API request timed out."
            or llm_command_response.startswith("Unexpected error")
        ):
            return (
                jsonify(
                    {
                        "error": "Error communicating with LLM.",
                        "details": llm_command_response,
                    }
                ),
                500,
            )
        else:
            llm_command = llm_command_response.strip()  # Get the raw command
            # remove any character except [. / a-z A-Z 0-9]
            llm_command = "".join(
                c for c in llm_command if c.isalnum() or c in [".", "/", " ", "-", "@"]
            )
            first_index = llm_command.find("app/scripts/")
            llm_command = "/" + llm_command[first_index:]

            try:
                # Security note: It's crucial to carefully validate and sanitize LLM outputs
                # before executing them. In a real-world scenario, more robust validation is needed.
                # For this project, we are assuming the LLM will follow instructions relatively well
                # given the constraints in the system prompt.

                process = subprocess.Popen(
                    llm_command,
                    shell=True,
                    executable="/bin/bash",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                stdout, stderr = process.communicate(
                    timeout=15
                )  # Set timeout for script execution

                stdout_decoded = stdout.decode("utf-8").strip()
                stderr_decoded = stderr.decode("utf-8").strip()

                response_data = {
                    "script_command": llm_command,
                    "script_output": stdout_decoded,
                    "script_error": stderr_decoded,
                }  # Log all outputs

                if process.returncode == 0:  # Script success
                    response_data["message"] = "Script executed successfully."
                    status_code = 200
                else:  # Script failed
                    response_data["message"] = "Script execution failed."
                    status_code = 500

                return jsonify(response_data), status_code

            except subprocess.TimeoutExpired:
                return (
                    jsonify(
                        {
                            "error": "Script execution timed out.",
                            "script_command": llm_command,
                        }
                    ),
                    500,
                )  # Agent error - script timed out
            except Exception as e:
                return (
                    jsonify(
                        {
                            "error": f"Error executing script: {e}",
                            "script_command": llm_command,
                        }
                    ),
                    500,
                )  # Agent error - general execution error
    else:  # Task description missing
        return jsonify({"error": "Task description is missing in the request."}), 400


@app.route("/read", methods=["GET"])
def read_file():
    user_path = request.args.get("path")
    if not user_path:
        return jsonify({"error": "File path is missing in the request."}), 400

    base_data_path = os.path.realpath(DATA_DIR)
    intended_path = os.path.realpath(os.path.join(DATA_DIR, user_path))

    if os.path.commonpath([base_data_path, intended_path]) != base_data_path:
        return (
            jsonify({"error": "Accessing path outside of /data is not allowed."}),
            400,
        )

    if not os.path.exists(intended_path):
        return jsonify({"error": "File not found."}), 404

    if not os.path.isfile(intended_path):
        # Check if the path is a directory
        if os.path.isdir(intended_path):
            # Return a list of files in the directory
            try:
                files = os.listdir(intended_path)
                return jsonify(files), 200
            except Exception as e:
                return jsonify({"error": f"Error listing directory: {e}"}), 500
        else:
            return jsonify({"error": "Path is not a file or dir."}), 400

    try:
        with open(intended_path, "r") as f:
            file_content = f.read()
        return file_content, 200, {"Content-Type": "text/plain"}
    except Exception as e:
        return jsonify({"error": f"Error reading file: {e}"}), 500


@app.route("/")
def hello():
    return "Hello from your LLM Automation Agent!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
