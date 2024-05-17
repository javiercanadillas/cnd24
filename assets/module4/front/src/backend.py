import os

import google.auth.transport.requests
import google.oauth2.id_token

def get_id_token(back_service_url: str) -> str:
  """
  new_request creates a new HTTP request with IAM ID Token credential.
  This token is automatically handled by private Cloud Run (fully managed)
  and Cloud Functions.
  """
  credentials, project = google.auth.default()
  auth_req = google.auth.transport.requests.Request()
  target_audience = back_service_url

  return google.oauth2.id_token.fetch_id_token(auth_req, target_audience)
