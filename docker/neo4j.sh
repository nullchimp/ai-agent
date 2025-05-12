#!/bin/bash

# Script to build and run the Neo4j Docker service for AI Agent
# This script manages the Neo4j database used by the AI Agent application

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

# Function to print colored output
print_message() {
    local color_code="$1"
    local message="$2"
    echo -e "\033[${color_code}m${message}\033[0m"
}

# Colors
GREEN=32
YELLOW=33
RED=31

print_message $GREEN "=== AI Agent Neo4j Database Management ==="

# Check for .env file and load environment variables if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    print_message $GREEN "Loading environment variables from .env file..."
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs -0 2>/dev/null || true)
else
    print_message $YELLOW "No .env file found. Using default credentials."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_message $RED "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    print_message $RED "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Parse command line arguments
ACTION=${1:-"start"}

case $ACTION in
    start)
        print_message $GREEN "Starting Neo4j database..."
        docker compose up -d
        print_message $GREEN "Neo4j is starting. It will be available at:"
        print_message $GREEN "- Browser interface: http://localhost:7474"
        print_message $GREEN "- Bolt connection: bolt://localhost:7687"
        print_message $GREEN "- Default credentials: ${NEO4J_USERNAME}/${NEO4J_PASSWORD}"
        ;;
        
    stop)
        print_message $YELLOW "Stopping Neo4j database..."
        docker compose down
        print_message $GREEN "Neo4j database stopped."
        ;;
        
    restart)
        print_message $YELLOW "Restarting Neo4j database..."
        docker compose down
        docker compose up -d
        print_message $GREEN "Neo4j database restarted."
        ;;
        
    status)
        print_message $GREEN "Checking Neo4j database status..."
        docker compose ps
        ;;
        
    logs)
        print_message $GREEN "Showing Neo4j logs..."
        docker compose logs -f
        ;;
        
    clean)
        print_message $RED "WARNING: This will remove all Neo4j data volumes!"
        read -p "Are you sure you want to continue? [y/N] " response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_message $YELLOW "Removing Neo4j database and volumes..."
            docker compose down -v
            print_message $GREEN "Neo4j database and volumes removed."
        else
            print_message $GREEN "Operation cancelled."
        fi
        ;;
        
    *)
        print_message $GREEN "Usage: $0 [start|stop|restart|status|logs|clean]"
        print_message $GREEN ""
        print_message $GREEN "Commands:"
        print_message $GREEN "  start   - Start the Neo4j database (default)"
        print_message $GREEN "  stop    - Stop the Neo4j database"
        print_message $GREEN "  restart - Restart the Neo4j database"
        print_message $GREEN "  status  - Check the status of the Neo4j database"
        print_message $GREEN "  logs    - Show logs from the Neo4j database"
        print_message $GREEN "  clean   - Remove the Neo4j database and volumes (destructive)"
        exit 1
        ;;
esac