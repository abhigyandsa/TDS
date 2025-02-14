# app.py
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/run', methods=['POST'])
def run_task():
    task_description = request.args.get('task')
    if task_description:
        # Placeholder - Task execution logic will go here
        response_data = {"message": f"Task received: {task_description}. Task execution not yet implemented."}
        return jsonify(response_data), 200
    else:
        return jsonify({"error": "Task description is missing in the request."}), 400

@app.route('/read', methods=['GET'])
def read_file():
    file_path = request.args.get('path')
    if file_path:
        try:
            # Basic placeholder for file reading - needs to be secured and limited to /data
            with open(file_path, 'r') as f:
                file_content = f.read()
            return file_content, 200, {'Content-Type': 'text/plain'} # Set content type to plain text
        except FileNotFoundError:
            return jsonify({"error": "File not found."}), 404
        except Exception as e:
            return jsonify({"error": f"Error reading file: {e}"}), 500
    else:
        return jsonify({"error": "File path is missing in the request."}), 400

@app.route('/') # Just for a basic "hello" message to check if the app is running
def hello():
    return "Hello from your LLM Automation Agent!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True) # Run on all interfaces, port 8000 for Docker, debug for local development
