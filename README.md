# PostgreSQL High Availability with HAProxy and Discord Bot

This project sets up a PostgreSQL high availability cluster with HAProxy for load balancing and includes a Discord bot for interacting with the database. The setup includes:

- 1 PostgreSQL master server (for write operations)
- 2 PostgreSQL slave servers (for read operations)
- 1 HAProxy server (for load balancing)
- A Discord bot for interacting with the PostgreSQL cluster

## Architecture

- **Master (192.168.56.10)**: Handles all write operations
- **Slaves (192.168.56.11, 192.168.56.12)**: Handle read operations
- **HAProxy (192.168.56.13)**: Routes traffic between master and slaves
  - Port 5000: Write operations (to master)
  - Port 5001: Read operations (load balanced between slaves)

## Quick Start

Use the automated startup script to set up and run the entire project:

```bash
./start_project.sh
```

This script will:
1. Start all the virtual machines using Vagrant
2. Set up the PostgreSQL database
3. Create/activate a Python virtual environment and install dependencies
4. Start the Discord bot

## Manual Setup

If you prefer to set up components individually:

1. Start the VMs:
   ```
   vagrant up
   ```

2. Deploy the configuration:
   ```
   ansible-playbook -i inventory.ini playbook.yml
   ```

3. Set up the database:
   ```
   ./setup_database.sh
   ```

4. Create a Python virtual environment and install dependencies:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. Start the Discord bot:
   ```
   python discord_bot.py
   ```

## Discord Bot Commands

The Discord bot provides the following slash commands:

- `/ping`: Test if the bot is working
- `/write <message>`: Write a message to the PostgreSQL master
- `/read`: Read the last 10 messages from PostgreSQL slaves (demonstrates load balancing)
- `/create_table`: Create the necessary database table if it doesn't exist

## Connecting to PostgreSQL Directly

- For write operations (INSERT, UPDATE, DELETE):
  ```
  psql -h 192.168.56.13 -p 5000 -U [username] -d [database]
  ```

- For read operations (SELECT):
  ```
  psql -h 192.168.56.13 -p 5001 -U [username] -d [database]
  ```

## HAProxy Statistics

View HAProxy stats:
- Open a web browser and navigate to: `http://192.168.56.13:8080`
- Login with username: `admin` and password: `admin`

## Testing the PostgreSQL Setup

SSH into the HAProxy server and run the test script:

```
vagrant ssh haproxy
sudo /root/test_postgres_connections.sh
```

This will test connections to both the master and slave servers through HAProxy.

## Notes

- The PostgreSQL replication is configured in streaming mode
- HAProxy health checks ensure only healthy servers receive traffic
- If the master goes down, you'll need to manually promote a slave to master
- The Discord bot token and database credentials are stored in the `.env` file (not committed to version control)
- The Discord bot demonstrates the load balancing by showing which slave server processed each read request
