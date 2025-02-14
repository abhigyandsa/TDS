import requests
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATA_DIR = "/data"  # Define the base /data directory inside the container

AIPROXY_URL = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")  # Load token from environment
LLM_MODEL_NAME = "gpt-4o-mini"


def call_llm(prompt):
    headers = {
        "Content-Type": "application/json",  # Updated header - no "Authorization" in Content-Type
        "Authorization": f"Bearer {AIPROXY_TOKEN}",  # Authorization header is separate
    }
    data = {
        "model": LLM_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
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
        prompt = task_description.strip()

        llm_response = call_llm(prompt)  # Call the LLM

        if (
            llm_response.startswith("Error calling LLM API")
            or llm_response == "LLM API request timed out."
            or llm_response.startswith("Unexpected error")
        ):
            return (
                jsonify(
                    {
                        "error": "Error communicating with LLM.",
                        "details": llm_response,
                    }
                ),
                500,
            )  # Agent Error
        else:
            # For now, just return the LLM response in the API response
            response_data = {
                "message": "LLM response received.",
                "llm_response": llm_response,
            }
            return jsonify(response_data), 200
    else:
        return jsonify({"error": "Task description is missing in the request."}), 400


@app.route("/read", methods=["GET"])
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
