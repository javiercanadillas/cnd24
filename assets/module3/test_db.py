# Description: Test database connection
from connect_connector import connect_with_connector
import sqlalchemy

from base_logger import logger

db = connect_with_connector()

with db.connect() as db_conn:
  logger.info("Querying 'votes' table")
  # Read from the votes table
  results = db_conn.execute(sqlalchemy.text('SELECT * FROM votes')).fetchall()

  # Show the results of the SELECT statement
  for row in results:
    print(row)