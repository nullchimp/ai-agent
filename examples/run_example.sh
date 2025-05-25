#!/bin/bash

# Set error handling
set -e

# Script to run example Python scripts in the ai-agent project
# Usage: ./run_example.sh <example_number> [--init]
# Example: ./run_example.sh 1  # Runs 1-chat.py without setting up environment
# Example: ./run_example.sh 1 --init  # Runs 1-chat.py with environment setup

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to setup and activate virtual environment
setup_venv() {
    echo "Setting up virtual environment..."
    
    # Check if virtual environment exists
    if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "${PROJECT_ROOT}/.venv"
    fi
    
    # Activate virtual environment
    echo "Activating virtual environment..."
    source "${PROJECT_ROOT}/.venv/bin/activate"
    
    # Install dependencies if requirements.txt exists
    if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
        echo "Installing dependencies..."
        pip install -r "${PROJECT_ROOT}/requirements.txt"
    else
        echo "Warning: requirements.txt not found in project root."
    fi
}

# Default to not initializing environment
init_env=false

# Check if --init flag was passed
if [ "$2" == "--init" ]; then
    init_env=true
    echo "Flag --init detected. Will initialize virtual environment."
fi

# Check if example number is provided
if [ $# -eq 0 ]; then
    echo "Error: Example number not provided."
    echo "Usage: ./run_example.sh <example_number> [--init]"
    echo "Available examples:"
    echo "  1 - Chat example (1-chat.py)"
    echo "  2 - Tool example (2-tool.py)"
    echo "  3 - Chat with tools example (3-chat-with-tools.py)"
    echo "  4 - Chat with tools and MCP example (4-chat-with-tools-and-mcp.py)"
    echo "  5 - Neo4j example (5-neo4j.py)"
    exit 1
fi

# Extract example number
example_num=$1

# Construct script name
script_name="${example_num}-"

# Find matching script in the examples directory
matching_script=""
for file in $(ls "${SCRIPT_DIR}" | grep "^${script_name}.*\.py$"); do
    matching_script=$file
    break
done

if [ -z "$matching_script" ]; then
    echo "Error: No example script found with number ${example_num}."
    echo "Available scripts:"
    ls "${SCRIPT_DIR}" | grep -E "^[0-9]+-.*\.py$"
    exit 1
fi

# Setup virtual environment only if the --init flag is provided
if [ "$init_env" = true ]; then
    setup_venv
    use_venv=true
else
    echo "Skipping environment initialization. Use --init flag to set up the environment."
    
    # Check if virtual environment exists and activate it if it does
    if [ -d "${PROJECT_ROOT}/.venv" ]; then
        echo "Using existing virtual environment..."
        source "${PROJECT_ROOT}/.venv/bin/activate"
        use_venv=true
    else
        echo "Warning: No virtual environment found. Script may fail if dependencies are not installed globally."
        use_venv=false
    fi
fi

# Print info
echo ""
echo ""
echo "Running example: ${matching_script}"

# Run the script (making sure we're in the examples directory)
cd "${SCRIPT_DIR}"
python3 "${matching_script}"

# Deactivate virtual environment only if it was activated
if [ "$use_venv" = true ]; then
    deactivate
    echo "Virtual environment deactivated."
fi

echo "Example execution completed."