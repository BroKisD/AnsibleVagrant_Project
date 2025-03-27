# PostgreSQL High Availability with HAProxy

This project sets up a PostgreSQL high availability cluster with HAProxy for load balancing. The setup includes:

- 1 PostgreSQL master server (for write operations)
- 2 PostgreSQL slave servers (for read operations)
- 1 HAProxy server (for load balancing)

## Architecture

- **Master (192.168.56.10)**: Handles all write operations
- **Slaves (192.168.56.11, 192.168.56.12)**: Handle read operations
- **HAProxy (192.168.56.13)**: Routes traffic between master and slaves

## Load Balancing Strategy

HAProxy is configured to:
- Route all write requests (port 5000) to the master
- Route all read requests (port 5001) to the slaves using round-robin algorithm

## How to Use

1. Start the VMs:
   ```
   vagrant up
   ```

2. Deploy the configuration:
   ```
   ansible-playbook -i inventory.ini playbook.yml
   ```

3. Connect to PostgreSQL:
   - For write operations (INSERT, UPDATE, DELETE):
     ```
     psql -h 192.168.56.13 -p 5000 -U [username] -d [database]
     ```
   
   - For read operations (SELECT):
     ```
     psql -h 192.168.56.13 -p 5001 -U [username] -d [database]
     ```

4. View HAProxy stats:
   - Open a web browser and navigate to: `http://192.168.56.13:8080`
   - Login with username: `admin` and password: `admin`

## Testing the Setup

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
