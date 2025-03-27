# Discord Bot for PostgreSQL High Availability

This Discord bot demonstrates the PostgreSQL high availability setup with HAProxy load balancing. It allows you to write data to the master server and read data from the slave servers through Discord commands.

## Features

- `/write [message]` - Writes a message to the PostgreSQL master database
- `/read` - Reads messages from PostgreSQL slave servers (load balanced)
- `/create_table` - Creates the required database table if it doesn't exist

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- PostgreSQL high availability setup with HAProxy (already configured)
- Discord bot token (already in .env file)

### Installation

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

2. Create the database table:

```bash
./setup_database.sh
```

### Running the Bot

Start the Discord bot:

```bash
python discord_bot.py
```

## How It Works

1. **Write Operations**: When you use the `/write` command, the bot connects to HAProxy on port 5000, which forwards the request to the PostgreSQL master server. The message is stored in the database along with information about which server processed it.

2. **Read Operations**: When you use the `/read` command, the bot connects to HAProxy on port 5001, which load balances the request between the PostgreSQL slave servers. The response includes information about which slave server processed the request.

## Security Note

The Discord bot token in the `.env` file should be kept secure. If you believe your token has been compromised, you should reset it immediately in the Discord Developer Portal.

## Troubleshooting

- If the bot cannot connect to the database, make sure your HAProxy and PostgreSQL servers are running.
- If commands aren't working, ensure the bot has the necessary permissions in your Discord server.
- Check the console output for error messages that might help diagnose issues.

## Architecture

- **HAProxy Server**: 192.168.56.13
  - Write Port: 5000 (forwards to master)
  - Read Port: 5001 (load balances between slaves)
- **PostgreSQL Master**: 192.168.56.10
- **PostgreSQL Slaves**: 192.168.56.11, 192.168.56.12
