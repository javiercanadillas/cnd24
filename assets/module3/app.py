import datetime
import os
from typing import Dict

from flask import Flask, render_template, request, Response

import sqlalchemy

from connect_connector import connect_with_connector
from base_logger import logger

app = Flask(__name__)


def init_connection_pool() -> sqlalchemy.engine.base.Engine:
  # Use the connector when INSTANCE_CONNECTION_NAME
  # (e.g. project:region:instance) is defined
  if os.environ.get("INSTANCE_CONNECTION_NAME"):
    logger.info("Using Cloud SQL connector")
    return connect_with_connector()

  raise ValueError("Missing database connection INSTANCE_CONNECTION_NAME")


# Initialize the connection pool when the application starts
with app.app_context():
  global db
  logger.info("Initiating connection pool")
  db = init_connection_pool()


@app.route("/", methods=["GET"])
def render_index() -> str:
  logger.info("Received request for the index page")
  context = get_index_context(db)
  return render_template("index.html", **context)


@app.route("/votes", methods=["POST"])
def cast_vote() -> Response:
    logger.info("Received vote from the frontend")
    team = request.form["team"]
    return save_vote(db, team)


# get_index_context gets data required for rendering HTML application
def get_index_context(db: sqlalchemy.engine.base.Engine) -> Dict:
  logger.info("Querying votes")
  votes = []

  with db.connect() as conn:
    # Execute the query and fetch all results
    recent_votes = conn.execute(
      sqlalchemy.text(
          "SELECT candidate, time_cast FROM votes ORDER BY time_cast DESC LIMIT 5"
      )
    ).fetchall()
    # Convert the results into a list of dicts representing votes
    for row in recent_votes:
      votes.append({"candidate": row[0], "time_cast": row[1]})

    stmt = sqlalchemy.text(
      "SELECT COUNT(vote_id) FROM votes WHERE candidate=:candidate"
    )
    # Count number of votes for tabs
    tab_count = conn.execute(stmt, parameters={"candidate": "TABS"}).scalar()
    # Count number of votes for spaces
    space_count = conn.execute(stmt, parameters={"candidate": "SPACES"}).scalar()

  return {
    "space_count": space_count,
    "recent_votes": votes,
    "tab_count": tab_count,
  }


# save_vote saves a vote to the database that was retrieved from form data
def save_vote(db: sqlalchemy.engine.base.Engine, team: str) -> Response:
  logger.info(f"Saving vote for '{team}'")
  time_cast = datetime.datetime.now(tz=datetime.timezone.utc)
  # Verify that the team is one of the allowed options
  if team != "TABS" and team != "SPACES":
    logger.warning(f"Received invalid 'team' property: '{team}'")
    return Response(
      response="Invalid team specified. Should be one of 'TABS' or 'SPACES'",
      status=400,
    )

  # [START cloud_sql_postgres_sqlalchemy_connection]
  # Preparing a statement before hand can help protect against injections.
  stmt = sqlalchemy.text(
    "INSERT INTO votes (time_cast, candidate) VALUES (:time_cast, :candidate)"
  )
  try:
    # Using a with statement ensures that the connection is always released
    # back into the pool at the end of statement (even if an error occurs)
    with db.connect() as conn:
        conn.execute(stmt, parameters={
          "time_cast": time_cast,
          "candidate": team})
        conn.commit()
  except Exception as e:
    # If something goes wrong, handle the error in this section. This might
    # involve retrying or adjusting parameters depending on the situation.
    logger.exception(e)
    return Response(
      status=500,
      response= "Unable to successfully cast vote! Please check the "
                "application logs for more details.",
    )
  # [END cloud_sql_postgres_sqlalchemy_connection]

  return Response(
    status=200,
    response=f"Vote successfully cast for '{team}' at time {time_cast}!",
  )


if __name__ == "__main__":
  app.run(host="127.0.0.1", port=8080, debug=True)
