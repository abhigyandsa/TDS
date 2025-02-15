#! /bin/bash

podman run -d -p 8000:8000 --name llm-agent-container --env-file .env llm-automation-agent-image 
