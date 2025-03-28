#!/bin/bash

# PostgreSQL High Availability with HAProxy and Discord Bot Startup Script
# This script automates the process of setting up and running the entire project

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print fatal error messages and exit
print_fatal_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Function to print info messages
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to show the main menu
show_menu() {
    print_section "PostgreSQL High Availability Demo Options"
    echo "1. Run Discord Bot (requires internet connection)"
    echo "2. Run CLI Demo (works offline)"
    echo "3. Exit"
    echo ""
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            start_discord_bot
            ;;
        2)
            start_cli_demo
            ;;
        3)
            print_info "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please try again."
            show_menu
            ;;
    esac
}

# Function to start the Discord bot
start_discord_bot() {
    print_section "Starting Discord Bot"
    print_info "The bot will run in the foreground. Press Ctrl+C to stop."
    print_info "Discord bot commands: /ping, /write, /read, /create_table"
    
    # Check if we can reach Discord's API
    print_info "Testing connection to Discord API..."
    if ! curl -s --connect-timeout 5 https://discord.com/api/v10 > /dev/null; then
        print_error "Cannot connect to Discord API. Please check your internet connection."
        print_info "Would you like to try the CLI demo instead? (y/n)"
        read -p "> " choice
        if [[ $choice == "y" || $choice == "Y" ]]; then
            start_cli_demo
        else
            show_menu
        fi
        return
    fi
    
    # Try to run the Discord bot
    python discord_bot.py
    
    # If we get here, the bot has exited
    print_info "Discord bot has stopped. Would you like to return to the menu? (y/n)"
    read -p "> " choice
    if [[ $choice == "y" || $choice == "Y" ]]; then
        show_menu
    fi
}

# Function to run the CLI demo
start_cli_demo() {
    print_section "Starting CLI Demo"
    
    # Check if cli_demo.py exists
    if [ ! -f "cli_demo.py" ]; then
        print_info "Creating CLI demo script..."
        cat > cli_demo.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import psycopg2
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('.env')
PG_HOST = os.getenv('PG_HOST')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_DATABASE = os.getenv('PG_DATABASE')
PG_WRITE_PORT = int(os.getenv('PG_WRITE_PORT'))
PG_READ_PORT = int(os.getenv('PG_READ_PORT'))

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print("\n===== PostgreSQL High Availability Demo =====")
    print("This demo shows how HAProxy load balances between PostgreSQL servers")
    print("==============================================\n")

def get_write_connection():
    try:
        print(f"Connecting to write database at {PG_HOST}:{PG_WRITE_PORT}")
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_WRITE_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        print("Successfully connected to write database")
        return conn
    except Exception as e:
        print(f"Error connecting to master database: {e}")
        return None

def get_read_connection():
    try:
        print(f"Connecting to read database at {PG_HOST}:{PG_READ_PORT}")
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_READ_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        print("Successfully connected to read database")
        return conn
    except Exception as e:
        print(f"Error connecting to slave database: {e}")
        return None

def get_server_info(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT inet_server_addr()::text, inet_server_port()::text;")
        server_addr, server_port = cursor.fetchone()
        cursor.close()
        return f"{server_addr}:{server_port}"
    except Exception as e:
        print(f"Error getting server info: {e}")
        return "Unknown"

def create_table():
    print("\n--- Creating Table ---")
    conn = get_write_connection()
    if not conn:
        print("Failed to connect to the master database.")
        return
    
    try:
        cursor = conn.cursor()
        
        # Create the table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS discord_messages (
            id SERIAL PRIMARY KEY,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            server_info TEXT
        );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Table 'discord_messages' created successfully!")
    except Exception as e:
        print(f"Error creating table: {e}")
        if conn:
            conn.close()

def write_message():
    print("\n--- Write Message to Master ---")
    message = input("Enter message to write: ")
    
    conn = get_write_connection()
    if not conn:
        print("Failed to connect to the master database.")
        return
    
    try:
        cursor = conn.cursor()
        server_info = get_server_info(conn)
        print(f"Connected to server: {server_info}")
        
        # Insert the message into the database
        cursor.execute(
            "INSERT INTO discord_messages (message, server_info) VALUES (%s, %s) RETURNING id;",
            (message, server_info)
        )
        message_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Message successfully written to master database with ID: {message_id}")
        print(f"Server: {server_info}")
    except Exception as e:
        print(f"Error writing to database: {e}")
        if conn:
            conn.close()

def read_messages():
    print("\n--- Read Messages from Slaves ---")
    
    conn = get_read_connection()
    if not conn:
        print("Failed to connect to the slave database.")
        return
    
    try:
        cursor = conn.cursor()
        server_info = get_server_info(conn)
        print(f"Connected to server: {server_info}")
        
        # Retrieve all messages from the database
        cursor.execute("SELECT id, message, created_at, server_info FROM discord_messages ORDER BY created_at DESC LIMIT 10;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            print(f"No messages found in the database.\nRead from: {server_info}")
            return
        
        print(f"Last 10 messages (read from {server_info}):")
        print("-" * 80)
        for row in rows:
            id, message, created_at, write_server = row
            print(f"ID: {id} | Message: {message} | Written at: {created_at} | Written by: {write_server}")
        print("-" * 80)
    except Exception as e:
        print(f"Error reading from database: {e}")
        if conn:
            conn.close()

def demonstrate_load_balancing():
    print("\n--- Demonstrating Load Balancing ---")
    print("Making multiple read requests to show load balancing between slaves...")
    
    for i in range(5):
        print(f"\nRequest {i+1}:")
        conn = get_read_connection()
        if not conn:
            print("Failed to connect to the slave database.")
            continue
        
        try:
            server_info = get_server_info(conn)
            print(f"Connected to server: {server_info}")
            conn.close()
            time.sleep(1)  # Short delay between requests
        except Exception as e:
            print(f"Error: {e}")
            if conn:
                conn.close()

def main_menu():
    while True:
        print_header()
        print("1. Create table (if not exists)")
        print("2. Write message to master")
        print("3. Read messages from slaves")
        print("4. Demonstrate load balancing")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            create_table()
        elif choice == '2':
            write_message()
        elif choice == '3':
            read_messages()
        elif choice == '4':
            demonstrate_load_balancing()
        elif choice == '5':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main_menu()
EOF
        chmod +x cli_demo.py
        print_success "CLI demo script created"
    fi
    
    # Run the CLI demo
    python cli_demo.py
    
    # If we get here, the CLI demo has exited
    print_info "CLI demo has stopped. Would you like to return to the menu? (y/n)"
    read -p "> " choice
    if [[ $choice == "y" || $choice == "Y" ]]; then
        show_menu
    fi
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_fatal_error ".env file not found. Please create it with the required environment variables."
fi

# Step 1: Start the virtual machines with Vagrant
print_section "Starting Virtual Machines with Vagrant"
print_info "This may take several minutes..."
vagrant up
if [ $? -ne 0 ]; then
    print_fatal_error "Failed to start virtual machines. Please check the Vagrant output for errors."
fi
print_success "Virtual machines started successfully"

# Step 2: Wait for a moment to ensure all VMs are fully booted
print_info "Waiting for VMs to complete boot process..."
sleep 30

# Step 3: Check if all VMs are running
print_section "Checking VM Status"
vagrant status
if [ $? -ne 0 ]; then
    print_fatal_error "Failed to get VM status. Please check the Vagrant output for errors."
fi

# Step 4: Set up the database
print_section "Setting up the PostgreSQL Database"
./setup_database.sh
if [ $? -ne 0 ]; then
    print_fatal_error "Failed to set up the database. Please check the output for errors."
fi
print_success "Database setup completed successfully"

# Step 5: Activate Python virtual environment if it exists
print_section "Setting up Python Environment"
if [ -d "venv" ]; then
    print_info "Activating virtual environment..."
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        print_fatal_error "Failed to activate virtual environment."
    fi
    print_success "Virtual environment activated"
else
    print_info "Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        print_fatal_error "Failed to create and activate virtual environment."
    fi
    print_success "Virtual environment created and activated"
    
    print_info "Installing required Python packages..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        print_fatal_error "Failed to install required Python packages."
    fi
    print_success "Python packages installed successfully"
fi

# Step 6: Show menu with options
show_menu
