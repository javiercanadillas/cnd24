Deploy the `front` service assigning the recently created `front-sa` service account identity to it and the `BACK_SERVICE_URL` environment variable:

```bash
gcloud run deploy front \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --service-account front-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars BACK_SERVICE_URL=$BACK_SERVICE_URL
  ```