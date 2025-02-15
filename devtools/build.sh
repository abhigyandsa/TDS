#! /bin/bash

podman build -t llm-automation-agent-image .
podman stop llm-agent-container
podman rm llm-agent-container
