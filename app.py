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
    Description: Installs 'uv' (if required) and runs the 'datagen.py' script to generate data files in the /data directory.
    Usage: /app/scripts/a1.sh
    - uv is installed by this script itself. No need to install it separately.
    - This script does not accept any arguments when invoked. Ignore instructions to pass arguments. It internally uses a predefined email and data root directory.
    - It will generate data files within the /data directory, which are required for other tasks.

    **Script: a3.sh**
    Description: Counts the number of occurrences of a specific day of the week in a file containing dates (one date per line).
    Usage: /app/scripts/a3.sh <day_of_week> <input_file> <output_file>
    - <day_of_week>: The day of the week to count (e.g., Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday). Case-insensitive. Should provide the day in English only. Translate if required.
    - <input_file>:  Path to the input file within the /data directory.
    - <output_file>: Path to the output file within the /data directory where the count will be written.

    **Constraints:**

    - All input and output files MUST be within the /data directory.
    - You MUST generate a single bash command line to execute the script with the correct arguments (if any).
    - Do not generate any explanatory text before or after the command. Only output the raw bash command.
    - Assume the scripts are already executable in the /app/scripts directory.

    Example Task for a3.sh: "Count the number of Fridays in /data/dates.txt and write the count to /data/friday_counts.txt"
    Example Command for a3.sh: /app/scripts/a3.sh Friday /data/dates.txt /data/friday_counts.txt

    Example Task for a1.sh: "Generate data files" or "Run data generation script" or "Install uv and run datagen.py with user@email.com"
    Example Command for a1.sh: /app/scripts/a1.sh
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
                    timeout=10
                )  # Set timeout for script execution

                if process.returncode == 0:  # Script executed successfully
                    response_data = {
                        "message": "Task A3 executed successfully.",
                        "script_command": llm_command,
                    }
                    return jsonify(response_data), 200
                else:  # Script failed
                    error_message = (
                        stdout.decode("utf-8").strip()
                        + "\n"
                        + stderr.decode("utf-8").strip()
                    )
                    return (
                        jsonify(
                            {
                                "error": "Script execution failed.",
                                "script_command": llm_command,
                                "script_error": error_message,
                            }
                        ),
                        500,
                    )  # Agent error - script itself failed

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

    # if os.path.commonpath([base_data_path, intended_path]) != base_data_path:
    #     return (
    #         jsonify({"error": "Accessing path outside of /data is not allowed."}),
    #         400,
    #     )

    if not os.path.exists(intended_path):
        return jsonify({"error": "File not found."}), 404

    if not os.path.isfile(intended_path):
        return jsonify({"error": "Path is not a file."}), 400

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
