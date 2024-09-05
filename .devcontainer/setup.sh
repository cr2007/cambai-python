#!/bin/bash

# Install Poetry
curl -sSL https://install.python-poetry.org | python - -y

# Update Poetry configuration
poetry config virtualenv.create false

# Install dependencies
poetry install --no-root
