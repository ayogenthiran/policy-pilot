#!/bin/bash

# Policy Pilot Docker Setup Script
# This script helps you set up and run the Policy Pilot application with Docker

set -e

echo "🚀 Policy Pilot Docker Setup"
echo "=============================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "❌ .env.local file not found!"
    echo "⚠️  Please create a .env.local file with your API keys and configuration"
    echo "   Required variables:"
    echo "   - NEXT_PUBLIC_SUPABASE_URL"
    echo "   - NEXT_PUBLIC_SUPABASE_ANON_KEY"
    echo "   - OPENAI_API_KEY"
    echo ""
    echo "   After creating .env.local, run this script again."
    exit 1
fi

echo "✅ Environment file found"

# Function to check if services are running
check_services() {
    echo "🔍 Checking if services are running..."
    if docker-compose ps | grep -q "Up"; then
        echo "✅ Services are already running"
        return 0
    else
        echo "❌ Services are not running"
        return 1
    fi
}

# Function to start services
start_services() {
    echo "🚀 Starting services..."
    docker-compose up -d
    
    echo "⏳ Waiting for services to be ready..."
    sleep 10
    
    echo "✅ Services started successfully!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   - Next.js App: http://localhost:3000"
    echo "   - pgAdmin: http://localhost:5050 (admin@policy-pilot.local / admin)"
    echo ""
    echo "📊 To view logs: docker-compose logs -f"
    echo "🛑 To stop services: docker-compose down"
}

# Function to stop services
stop_services() {
    echo "🛑 Stopping services..."
    docker-compose down
    echo "✅ Services stopped"
}

# Function to rebuild services
rebuild_services() {
    echo "🔨 Rebuilding services..."
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    echo "✅ Services rebuilt and started"
}

# Main menu
show_menu() {
    echo ""
    echo "What would you like to do?"
    echo "1) Start services"
    echo "2) Stop services"
    echo "3) Rebuild services"
    echo "4) View logs"
    echo "5) Check service status"
    echo "6) Exit"
    echo ""
    read -p "Enter your choice (1-6): " choice
}

# Handle menu choices
case "${1:-}" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "rebuild")
        rebuild_services
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "")
        # Interactive mode
        while true; do
            show_menu
            case $choice in
                1)
                    start_services
                    ;;
                2)
                    stop_services
                    ;;
                3)
                    rebuild_services
                    ;;
                4)
                    docker-compose logs -f
                    ;;
                5)
                    docker-compose ps
                    ;;
                6)
                    echo "👋 Goodbye!"
                    exit 0
                    ;;
                *)
                    echo "❌ Invalid choice. Please try again."
                    ;;
            esac
        done
        ;;
    *)
        echo "Usage: $0 [start|stop|rebuild|logs|status]"
        echo "   Or run without arguments for interactive mode"
        exit 1
        ;;
esac 