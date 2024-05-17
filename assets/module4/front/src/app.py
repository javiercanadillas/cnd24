import os

from flask import Flask, render_template, request
import requests

from base_logger import logger
from backend import get_id_token

# This is the backend service URL in the form https://my-cloud-run-service.run.app
back_service_url = os.environ.get("BACK_SERVICE_URL", "http//localhost:8080")
if not back_service_url:
  raise Exception("BACK_SERVICE_URL missing")

app = Flask(__name__)
id_token = get_id_token(back_service_url)

headers = {
  "Authorization": f"Bearer {id_token}",
}

@app.route('/', methods=["GET"])
def render_index() -> str:
  db_data = requests.get(
              f"{back_service_url}/get_votes", headers=headers
            ).json()["data"]
  logger.info(f"Received data from backend: {db_data}")
  return render_template("index.html", **db_data)


@app.route('/votes', methods=['POST'])
def cast_vote() -> str:
  logger.info("Received request to cast a vote. Calling the backend")
  content = request.get_json()
  logger.info(f"Request content: {content}")
  return requests.post(
           f"{back_service_url}/cast_vote", headers=headers, json=content
         ).json()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
