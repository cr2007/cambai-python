#!/bin/bash

# Install Poetry
curl -sSL https://install.python-poetry.org | python - -y

# Add Poetry to PATH (important in container environments)
export PATH="/home/vscode/.local/bin:$PATH"

# Check if Poetry was installed
if ! poetry --version; then
    echo "Poetry installation failed"
    exit 1
fi

# Install dependencies
poetry install
