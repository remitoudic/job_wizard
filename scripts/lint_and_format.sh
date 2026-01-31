#!/bin/bash
set -e

# Go to project root
cd "$(dirname "$0")/.."

echo "Linting and formatting code..."

echo "Processing Backend..."
cd backend
uvx ruff check --fix
uvx ruff format
cd ..

echo "Processing Database..."
cd database
uvx ruff check --fix
uvx ruff format
cd ..

echo "Done!"
