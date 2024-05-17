# [START cloud_sql_postgres_sqlalchemy_connect_connector]
import os

from google.cloud.sql.connector import Connector
import pg8000
import sqlalchemy

from base_logger import logger


def connect_with_connector() -> sqlalchemy.engine.base.Engine:
  """
  Initializes a connection pool for a Cloud SQL instance of Postgres.
  Uses the Cloud SQL Python Connector package.
  """
  # Get environment variables from environment
  logger.info("Getting environment variables")
  instance_connection_name  = os.environ["INSTANCE_CONNECTION_NAME"]
  db_user                   = os.environ["DB_USER"]
  db_pass                   = os.environ["DB_PASS"]
  db_name                   = os.environ["DB_NAME"]
  logger.info(
    "Connection data:\n"
    f"  Database   : {db_name}\n"
    f"  User/pass  : {db_user}/{db_pass}\n"
    f"  Conn string: {instance_connection_name}"
  )

  # initialize Cloud SQL Python Connector object
  logger.info("Initializing connector")
  connector = Connector()

  def getconn() -> pg8000.Connection:
    conn: pg8000.Connection = connector.connect(
      instance_connection_name,
      "pg8000",
      user=db_user,
      password=db_pass,
      db=db_name,
    )
    return conn

  # Create SQLAlchemy Engine Pool object
  logger.info("Creating connection pool")
  pool = sqlalchemy.create_engine(
    "postgresql+pg8000://",
    creator=getconn,
  )
  
  return pool
