import os

from google.cloud.sql.connector import Connector
from base_logger import logger
import sqlalchemy

# Initialize Connector object
logger.info("Initializing connector")
connector = Connector()

# Return a connection to the database
def getconn():
  instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]
  db_user = os.environ["DB_USER"]
  db_pass = os.environ["DB_PASS"]
  db_name = os.environ["DB_NAME"]
  logger.info( "Connection data:\n"
                f"  Database   : {db_name}\n"
                f"  User/pass  : {db_user}/{db_pass}\n"
                f"  Conn string: {instance_connection_name}")
  try:
    conn = connector.connect(
      instance_connection_name,
      "pg8000",
      user=db_user,
      password=db_pass,
      db=db_name,
    )  
    return conn
  except Exception:
     logger.exception("Error creating connection pool")

# Create connection pool with creator argument to our connection object function
logger.info("Creating connection pool")
pool = sqlalchemy.create_engine(
  "postgresql+pg8000://",
  creator=getconn,
)

print("Connecting to the database")
with pool.connect() as db_conn:
  print("Creating 'votes' table")
  db_conn.execute(
    sqlalchemy.text(
        "CREATE TABLE IF NOT EXISTS votes "
        "( vote_id SERIAL NOT NULL, time_cast timestamp NOT NULL, "
        "candidate VARCHAR(6) NOT NULL, PRIMARY KEY (vote_id) );"
    )
  )

  print("Committing transaction")
  # Commit the transaction
  db_conn.commit()

  # Insert a row into the votes table
  insert_stmt = sqlalchemy.text(
      "INSERT INTO votes (time_cast, candidate) VALUES (NOW(), 'TABS')",
  )
  db_conn.execute(insert_stmt)

  db_conn.commit()

  # Read from the votes table
  results = db_conn.execute(sqlalchemy.text("SELECT * FROM votes")).fetchall()

  # Show the results of the SELECT statement
  for row in results:
      print(row)

# Clean up
connector.close()
