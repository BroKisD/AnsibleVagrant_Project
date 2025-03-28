import os
import discord
from discord import app_commands
import psycopg2
from dotenv import load_dotenv
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('discord_bot')

# Load environment variables
load_dotenv('.env')
TOKEN = os.getenv('DISCORD_TOKEN')
PG_HOST = os.getenv('PG_HOST')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_DATABASE = os.getenv('PG_DATABASE')
PG_WRITE_PORT = int(os.getenv('PG_WRITE_PORT'))
PG_READ_PORT = int(os.getenv('PG_READ_PORT'))

# Create a simple bot with minimal configuration
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Function to connect to PostgreSQL for write operations (master)
def get_write_connection():
    try:
        logger.info(f"Connecting to write database at {PG_HOST}:{PG_WRITE_PORT}")
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_WRITE_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        logger.info("Successfully connected to write database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to master database: {e}")
        return None

# Function to connect to PostgreSQL for read operations (slaves)
def get_read_connection():
    try:
        logger.info(f"Connecting to read database at {PG_HOST}:{PG_READ_PORT}")
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_READ_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        logger.info("Successfully connected to read database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to slave database: {e}")
        return None

# Function to get server information
def get_server_info(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT inet_server_addr()::text, inet_server_port()::text;")
        server_addr, server_port = cursor.fetchone()
        cursor.close()
        return f"{server_addr}:{server_port}"
    except Exception as e:
        logger.error(f"Error getting server info: {e}")
        return "Unknown"

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id})')
    
    # Get all guilds the bot is in
    for guild in client.guilds:
        logger.info(f"Bot is in guild: {guild.name} (ID: {guild.id})")
        
        # Register commands for this specific guild
        try:
            # First clear all existing commands to avoid conflicts
            tree.clear_commands(guild=discord.Object(id=guild.id))
            
            # Add commands
            @tree.command(name="ping", description="Test if the bot is working", guild=discord.Object(id=guild.id))
            async def ping_command(interaction: discord.Interaction):
                await interaction.response.send_message("Pong! Bot is working.")
                logger.info(f"Responded to ping from {interaction.user}")
            
            @tree.command(name="write", description="Write a message to PostgreSQL master", guild=discord.Object(id=guild.id))
            async def write_command(interaction: discord.Interaction, message: str):
                logger.info(f"Received /write command from {interaction.user} with message: {message}")
                await interaction.response.defer()
                
                conn = get_write_connection()
                if not conn:
                    await interaction.followup.send("Failed to connect to the master database.")
                    return
                
                try:
                    cursor = conn.cursor()
                    server_info = get_server_info(conn)
                    logger.info(f"Connected to server: {server_info}")
                    
                    # Insert the message into the database
                    cursor.execute(
                        "INSERT INTO discord_messages (message, server_info) VALUES (%s, %s) RETURNING id;",
                        (message, server_info)
                    )
                    message_id = cursor.fetchone()[0]
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    logger.info(f"Message written with ID: {message_id}")
                    await interaction.followup.send(f"✅ Message successfully written to master database with ID: {message_id}\nServer: {server_info}")
                except Exception as e:
                    logger.error(f"Error writing to database: {e}")
                    if conn:
                        conn.close()
                    await interaction.followup.send(f"❌ Error writing to database: {str(e)}")
            
            @tree.command(name="read", description="Read messages from PostgreSQL slaves", guild=discord.Object(id=guild.id))
            async def read_command(interaction: discord.Interaction):
                logger.info(f"Received /read command from {interaction.user}")
                await interaction.response.defer()
                
                conn = get_read_connection()
                if not conn:
                    logger.error("Failed to connect to the slave database")
                    await interaction.followup.send("Failed to connect to the slave database.")
                    return
                
                try:
                    cursor = conn.cursor()
                    server_info = get_server_info(conn)
                    logger.info(f"Connected to server: {server_info}")
                    
                    # Retrieve all messages from the database
                    cursor.execute("SELECT id, message, created_at, server_info FROM discord_messages ORDER BY created_at DESC LIMIT 10;")
                    rows = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    
                    if not rows:
                        logger.info("No messages found in the database")
                        await interaction.followup.send(f"No messages found in the database.\nRead from: {server_info}")
                        return
                    
                    # Format the results
                    messages = []
                    for row in rows:
                        id, message, created_at, write_server = row
                        messages.append(f"ID: {id} | Message: {message} | Written at: {created_at} | Written by: {write_server}")
                    
                    response = f"📚 Last 10 messages (read from {server_info}):\n\n" + "\n".join(messages)
                    logger.info(f"Returning {len(rows)} messages from server {server_info}")
                    await interaction.followup.send(response)
                except Exception as e:
                    logger.error(f"Error reading from database: {e}")
                    if conn:
                        conn.close()
                    await interaction.followup.send(f"❌ Error reading from database: {str(e)}")
            
            @tree.command(name="create_table", description="Create the discord_messages table", guild=discord.Object(id=guild.id))
            async def create_table_command(interaction: discord.Interaction):
                logger.info(f"Received /create_table command from {interaction.user}")
                await interaction.response.defer()
                
                conn = get_write_connection()
                if not conn:
                    await interaction.followup.send("Failed to connect to the master database.")
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
                    
                    logger.info("Table 'discord_messages' created successfully")
                    await interaction.followup.send("✅ Table 'discord_messages' created successfully!")
                except Exception as e:
                    logger.error(f"Error creating table: {e}")
                    if conn:
                        conn.close()
                    await interaction.followup.send(f"❌ Error creating table: {str(e)}")
            
            # Sync the commands
            await tree.sync(guild=discord.Object(id=guild.id))
            logger.info(f"Commands synced for guild: {guild.name}")
        except Exception as e:
            logger.error(f"Failed to sync commands for guild {guild.name}: {e}")
    
    logger.info('------')

# Run the bot
if __name__ == "__main__":
    logger.info("Starting Discord bot...")
    client.run(TOKEN)
