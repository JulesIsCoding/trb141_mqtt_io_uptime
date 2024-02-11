from sqlite3 import connect
from pathlib import Path

db_path = Path("/trb141_mqtt_io_uptime/trb141_db")

def query_db(sql, args=(), one=False):
    conn = connect(db_path)
    cur = conn.cursor()

    cur.execute(sql, args)
    rv = cur.fetchall()

    cur.close()
    conn.commit()
    conn.close()

    return (rv[0] if rv else None) if one else rv

def init_database(info_logger, error_logger):
    try:
        if Path.is_file(db_path) == False:
            # Create trb141_db file
            info_logger.info("Database has not been created.")
            info_logger.info(f"Creating new DB at {str(db_path)}")
            conn = connect(db_path)
            conn.close()
            info_logger.info("Database created.")

            # Create message table
            info_logger.info("Creating message table.")
            create_message_sql = "create table IF NOT EXISTS messages (\
                id INTEGER PRIMARY KEY, \
                name TEXT UNIQUE, \
                timestamp INTEGER, \
                numericValue INTEGER, \
                booleanValue BOOL);"
            query_db(create_message_sql)

            # Create persistent data table
            info_logger.info("Creating persistent data table")
            create_message_sql = "CREATE TABLE IF NOT EXISTS persistent_data (\
                id INTEGER PRIMARY KEY, \
                name TEXT UNIQUE, \
                timestamp INTEGER, \
                numericValue INTEGER, \
                booleanValue BOOL);"
            query_db(create_message_sql)

        else:
            info_logger.info("Database already created.")

    except Exception as e:
        error_logger.error(f"Migrations Failed: {e}")
        exit(1)

def get_persistent_data(error_logger):
    try:
        rows = query_db("SELECT * FROM persistent_data;")
        data_dict = {
            str(row[1]): {
                "timestamp": row[2],
                "numericValue": row[3],
                "booleanValue": row[4],
            }
            for row in rows
        }
        return data_dict
    except Exception as e:
        error_logger.error(f"Failed to fetch persistent data: {e}")
        return {}

def get_messages(error_logger):
    try:
        conn = connect(db_path)
        cur = conn.cursor()

        # Start a transaction
        cur.execute("BEGIN TRANSACTION;")

        # Fetch all messages
        cur.execute("SELECT * FROM messages;")
        rows = cur.fetchall()

        # Empty the 'messages' table
        cur.execute("DELETE FROM messages;")

        # Commit the transaction
        conn.commit()

        cur.close()
        conn.close()

        return rows
    except Exception as e:
        error_logger.error(f"Failed to fetch and clear messages: {e}")
        return []

def insert_or_update_persistent_data(reading, error_logger):
    try:
        name = reading["name"]
        timestamp = reading["timestamp"]
        numericValue = reading.get("numericValue")
        booleanValue = reading.get("booleanValue")

        insert_or_replace_sql = "INSERT OR REPLACE INTO persistent_data (name, timestamp, numericValue, booleanValue) VALUES (?, ?, ?, ?);"
        query_db(
            insert_or_replace_sql,
            (name, timestamp, numericValue, booleanValue),
        )
    except Exception as e:
        error_logger.error(f"Failed to insert or update persistent data: {e}")
