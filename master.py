import socket
import psycopg2
from config import *

def get_db_connection(host):
    return psycopg2.connect(
        host=host,
        database="postgres",
        user=PG_USER,
        password=PG_PASSWORD,
        port=PG_PORT
    )

def send_command(command, host=MASTER_HOST, port=MASTER_CONTROL_PORT):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((host, port))
        print(f"Connected to proxy at {host}:{port}")
        
        # Send command
        print(f"Sending command: {command}")
        client.send(command.encode())
        
        # Receive response
        response = client.recv(4096)
        print(f"Received response: {response.decode()}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

def check_db_status(host):
    try:
        conn = get_db_connection(host)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        cur.close()
        conn.close()
        return f"PostgreSQL connection successful. Version: {version[0]}"
    except Exception as e:
        return f"PostgreSQL connection failed: {str(e)}"

def main():
    print("Master Control Program")
    print("Available commands:")
    print("- time: Get current time from slave")
    print("- status: Get slave status")
    print("- dbstatus: Check PostgreSQL status")
    print("- master: Switch to master node")
    print("- slave1: Switch to slave1 node")
    print("- slave2: Switch to slave2 node")
    print("- quit: Exit the program")
    
    current_host = MASTER_HOST
    
    try:
        while True:
            command = input(f"\nEnter command [{current_host}]: ")
            if command.lower() == 'quit':
                break
            elif command.lower() == 'dbstatus':
                print(check_db_status(current_host))
            elif command.lower() == 'master':
                current_host = MASTER_HOST
                print(f"Switched to master node: {current_host}")
            elif command.lower() == 'slave1':
                current_host = SLAVE1_HOST
                print(f"Switched to slave1 node: {current_host}")
            elif command.lower() == 'slave2':
                current_host = SLAVE2_HOST
                print(f"Switched to slave2 node: {current_host}")
            else:
                send_command(command, current_host)
    except KeyboardInterrupt:
        print("\nShutting down master...")

if __name__ == "__main__":
    main()
