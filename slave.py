import socket
import time
import psycopg2
from config import *

def get_db_status():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user=PG_USER,
            password=PG_PASSWORD,
            port=PG_PORT
        )
        cur = conn.cursor()
        
        # Get PostgreSQL version
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        
        # Get replication status
        cur.execute("""
            SELECT client_addr, state, sync_state 
            FROM pg_stat_replication;
        """)
        replicas = cur.fetchall()
        
        cur.close()
        conn.close()
        
        status = f"PostgreSQL Version: {version}\n"
        if replicas:
            status += "Replication Status:\n"
            for replica in replicas:
                status += f"Client: {replica[0]}, State: {replica[1]}, Sync: {replica[2]}\n"
        else:
            status += "No active replications"
            
        return status
    except Exception as e:
        return f"Database Error: {str(e)}"

def start_slave(host='0.0.0.0', port=SLAVE_PORT):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Slave listening on {host}:{port}")

    try:
        while True:
            client_socket, addr = server.accept()
            print(f"Received connection from {addr}")
            
            while True:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    command = data.decode()
                    print(f"Slave received command: {command}")
                    
                    # Process the command
                    if command.lower() == 'time':
                        response = f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    elif command.lower() == 'status':
                        response = "Slave status: Running"
                    elif command.lower() == 'dbstatus':
                        response = get_db_status()
                    else:
                        response = f"Slave processed: {command}"
                    
                    print(f"Slave sending response: {response}")
                    client_socket.send(response.encode())
                except Exception as e:
                    print(f"Error in slave: {e}")
                    break
                    
            client_socket.close()
    except KeyboardInterrupt:
        print("Shutting down slave...")
        server.close()

if __name__ == "__main__":
    start_slave()
