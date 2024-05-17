# Splitting the monolith

In the previous module, you developed a Python Flask based Cloud Run application that connects to a database and performs different operations. The application renders a frontend that allows you to vote for TABS or SPACES, and also exposes an API that allows you to cast a vote and get the current votes. These two functions are closely interlinked, having no separation between the frontend and the backend in the code. This is a common pattern when developing applications, but it's not ideal for a number of reasons that we've discussed already.

You'll proceed now to split the application into two separate services, one for the frontend and one for the backend. You'll also secure the backend service by deploying it with the `no-allow-unauthenticated` option and also using Cloud Secret Manager to store the database credentials.

The `db-api` service will then be split into two different services:

  - `front`: this service will retain the Flask template. This template contains a small javascript script that queries the latest votes count whenever the page is loaded and that sends a `POST` request to the `back` service if a vote is cast containing a JSON file with the team name and the number of votes.
  - `back`: this service exposes a CRUD_ish_ API that allows you to cast a vote and get the current votes count. Delete and Update are not implemented as we want to keep the application simple.

To control the security of the services with some degree of detail, you'll assign different identities to each service. Cloud identities destined to Cloud Run services are called _service accounts_, and you'll be creating two of them, one for each service.

## Bootstrapping this module

This module builds on the work done in [Module 3](../module1/Module3.md).

If you have just finished Module 3 without stopping your Qwiklabs lab, there's nothing additional for you to do in this section and you should continue to [Preparing the new backend service](preparing-the-new-backend-service) section below.

However, **if you're starting fresh from a new Qwiklabs lab** because you did Module 3 some day in the past, you need to do the following steps to automatically replay the steps done in Module 3.

1. Open a new [Google Cloud Console](console.cloud.google.com) tab in your browser and log in with your Qwiklabs credentials.
   Accept the terms and activate the Qwiklabs project. 
2. Open a new [Google Cloud Shell](shell.cloud.google.com) in your Qwiklabs project. Set up your project and preferred region:
  ```bash
  gcloud config set project <your-qwiklabs-project-id>
  gcloud config set compute/region <your-preferred-cloud-region>
  ```
3. Clone this repo
  ```bash
  git clone https://github.com/javiercanadillas/cnd.git
  ```
4. Run Module 3 steps replay script:
  ```bash
  cd "$HOME/cnd/assets/module3" && ./module3_replay_steps.bash
  ``` 
5. As requested in the output of the previous script, source your `.bashrc` file
  ```bash
  source "$HOME/.bashrc"
  ```

Once all this has been done, you should be ready to continue with Module 4. Read on.

## Preparing the new backend service

The backend service is very similar to the `db-api` service you experienced with in [Module 3](../Module3.md). The difference is now that this service is a pure API with no frontend rendering that it's accepting JSON documents on two endpoints:

  -  `get_votes`: this endpoint accetps a `GET` and returns the current votes count in JSON format.
  -  `cast_vote`: this endpoint accepts a `POST`ed JSON document with the team name and the number of votes to cast.


Create the basic structure for the `back` service and copy the necessary files from the `back` service from assets:

```bash
cd $HOME/cnd
mkdir -p back/src
cp -r assets/module4/back/. back/
```

### Testing the `back` service locally

Source the proper environment variables to be able to run the service locally:

```bash
cd back
source .labenv_db
```

Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-local.txt
```

Launch the service locally:

```bash
cd src
python app.py
```

Open a new terminal and test the `get_votes` endpoint:

[Terminal 2]
```bash
curl -v localhost:8080/get_votes
```

You should get a response similar to this one:
```text
*   Trying 127.0.0.1:8080...
* Connected to localhost (127.0.0.1) port 8080 (#0)
> GET /get_votes HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.88.1
> Accept: */*
>
< HTTP/1.1 200 OK
< Server: Werkzeug/2.3.4 Python/3.11.2
< Date: Sat, 27 May 2023 13:27:51 GMT
< Content-Type: application/json
< Content-Length: 620
< Connection: close
<
{
  "data": {
    "recent_votes": [
      {
        "candidate": "TABS",
        "time_cast": "Mon, 22 May 2023 10:27:32 GMT"
      },
      {
        "candidate": "TABS",
        "time_cast": "Mon, 22 May 2023 10:06:57 GMT"
      },
      {
        "candidate": "TABS",
        "time_cast": "Sun, 21 May 2023 14:55:39 GMT"
      },
      {
        "candidate": "TABS",
        "time_cast": "Sun, 21 May 2023 14:55:31 GMT"
      },
      {
        "candidate": "TABS",
        "time_cast": "Sun, 21 May 2023 10:43:35 GMT"
      }
    ],
    "space_count": 5,
    "tab_count": 7
  },
  "message": "OK",
  "status": 200
}
* Closing connection 0
```

In the other terminal, you should see the logs of the `back` service:

[Terminal 1]
```text
INFO - Getting environment variables
INFO - Connection data:
  Database   : mydatabase
  User/pass  : postgres/postgres
  Conn string: javiercm-testing3:europe-west1:myinstance
INFO - Initializing connector
INFO - Creating connection pool
 * Serving Flask app 'app'
 * Debug mode: on
INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:8080
INFO - Press CTRL+C to quit
INFO -  * Restarting with stat
INFO - Getting environment variables
INFO - Connection data:
  Database   : mydatabase
  User/pass  : postgres/postgres
  Conn string: javiercm-testing3:europe-west1:myinstance
INFO - Initializing connector
INFO - Creating connection pool
WARNING -  * Debugger is active!
INFO -  * Debugger PIN: 478-674-331
INFO - Getting votes from database
INFO - 127.0.0.1 - - [27/May/2023 15:27:28] "GET /get_votes HTTP/1.1" 200 -
```

Now, test the `cast_vote` endpoint creating a new vote for the `SPACES` team. To do so, you'll need to send a `POST` request with a JSON document containing the team name from the terminal you opened before to issue curl commands:

[Terminal 2]
```bash
curl -X POST -H "Content-Type: application/json" -d '{"team": "SPACES"}' localhost:8080/cast_vote
```

You should see the response from the service:

[Terminal 2]
```text
{
  "message": "OK",
  "status": 200
}
```

If you go back to the terminal where the `back` service is running, you should see the logs of the service:

[Terminal 1]
```text
INFO - Receiving vote
INFO - Vote successfully inserted into the database for team SPACES
INFO - 127.0.0.1 - - [27/May/2023 15:45:56] "POST /cast_vote HTTP/1.1" 200 -
```

You can now close the terminal you were using to run the `curl` commands (Terminal 2), and press `CTRL+C` in the terminal where the `back` service is running to stop the service.

## Preparing the Cloud environment to deploy the services (aka, securing the `back` service)

To protect the services deployed in Cloud Run, you'll need to create a service account for the each of the `front` and `back` services:

```bash
service_list=("front" "back")
for service_name in "${service_list[@]}"; do
  sa_name="$service_name-sa"
  gcloud iam service-accounts create $sa_name --description="Service account for the $service_name service" --display-name=$sa_name
done
```

Then, grant yourself permission to impersonate the service accounts. This will allow you to deploy the services with your own user account, but the services will be assigned the service account identities:

```bash
for service_name in "${service_list[@]}"; do
  sa_name="$service_name-sa"
  echo $sa_name@$PROJECT_ID.iam.gserviceaccount.com
  gcloud iam service-accounts add-iam-policy-binding $sa_name@$PROJECT_ID.iam.gserviceaccount.com \
    --member user:$(gcloud config get-value account 2>/dev/null) \
    --role roles/iam.serviceAccountUser
done
```

Finally, you need to grant the `back` service permissions to access the Cloud SQL database (`roles/cloudsql.client`), which means granting the `back-sa` service account the `roles/cloudsql.client` role on the project:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:back-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role roles/cloudsql.client
```

## Deploying the `back` service onto Cloud Run

You're now ready to deploy the `back` service assigning the recently created `back-sa` service account identity to it.

Instead of using a regular `gcloud run deploy` command, you'll use a tool called `skaffold`. This tool is part of the binaries installed in the Cloud Shell, and it allows you to deploy your services in a more automated way.

One of the advantages of using Skaffold is that it will allow you to stream the application logs back to your terminal, so you can see the logs of the deployed Cloud Run service in real time.

Skaffold will use the `skaffold.yaml` file to know how to deploy the service. This file contains the configuration for the deployment, including the service account identity to use. It also relies on another environment configuration file called `skaffold.env` that contains the environment variables to use when deploying the service. To deploy a Cloud Run service, it will use the service yaml file in `resources/manifest.yaml`.

To use Skaffold, you'll first include the environment variables values in the three files mentioned above using `envsubst`:

```bash
cd $HOME/cnd/back
envsubst < skaffold.env.tmpl > skaffold.env
envsubst < skaffold.yaml.tmpl > skaffold.yaml
envsubst < resources/manifest.yaml.tmpl > resources/manifest.yaml
```

Then, you'll deploy the service using Skaffold with the following command:

[Terminal 1]
```bash
skaffold dev
```

Observe how Skaffold proceeds to build the container image, and then deploys the service. Once the service is deployed, you'll see the logs of the service in the terminal streaming back to you.

Leave that terminal open streaming the logs, and open a new terminal tab to test the service.

In this new terminal, get the service url and store it in the environment variable `BACK_SERVICE_URL`:

[Terminal 2]
```bash
BACK_SERVICE_URL=$(gcloud run services describe back --region $REGION --format="value(status.url)")
export BACK_SERVICE_URL
```

You also need to configure the receiving `back` service to accept requests from the `front` by making the calling service's service account a _principal_ on the receiving service. Then you grant the service account the Cloud Run Invoker (`roles/run.invoker`) role on the receiving service:

[Terminal 2]
```bash
gcloud run services add-iam-policy-binding back \
  --member=serviceAccount:front-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/run.invoker \
  --region $REGION
```

Test the `get_votes` endpoint, this time using OAuth authentication by opening a new tab and running the following command:

[Terminal 2]
```bash
curl -v $BACK_SERVICE_URL/get_votes \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

You should see the response from the service, similar to the one you got when testing the service locally:

[Terminal 2]
```text
[...]
server: Google Frontend
< content-length: 413
< alt-svc: h3=":443"; ma=2592000,h3-29=":443"; ma=2592000
<
{"data":{"recent_votes":[{"candidate":"SPACES","time_cast":"Sat, 27 May 2023 13:45:56 GMT"},{"candidate":"TABS","time_cast":"Mon, 22 May 2023 10:27:32 GMT"},{"candidate":"TABS","time_cast":"Mon, 22 May 2023 10:06:57 GMT"},{"candidate":"TABS","time_cast":"Sun, 21 May 2023 14:55:39 GMT"},{"candidate":"TABS","time_cast":"Sun, 21 May 2023 14:55:31 GMT"}],"space_count":6,"tab_count":7},"message":"OK","status":200}
* Connection #0 to host back-giunrmdkzq-ew.a.run.app left intact
```

As Skaffold is proxyfying the connection to the `back` service, you could've also done this to test the service:

[Terminal 2]
```bash
curl -v localhost:8081/get_votes
```

Note how thanks to the Cloud Run Proxy used by Skaffold you don't need to include the `Authorization` header in the request anymore.


## Deploying the `front` service onto Cloud Run

You're still running `skaffold dev` in Terminal 1, and you've been working in a second terminal (Terminal 2) where you tested the `back` service. You'll continue working now in **Terminal 2** to prepare the `front` service code assets and project structure:

[Terminal 2]
```bash
cd $HOME/cnd
mkdir -p front/src && cd front
cp -r ../assets/module4/front/. .
```

You'll deploy the `front` service using the same `skaffold.yaml` file you used for the `back` service, but you'll need to change the service account identity to use. That's already done for you, the only remaining thing is to include the environment variables values the same way you did for the `back` service:

[Terminal 2]
```bash
cd $HOME/cnd/front
envsubst < skaffold.env.tmpl > skaffold.env
envsubst < skaffold.yaml.tmpl > skaffold.yaml
envsubst < resources/manifest.yaml.tmpl > resources/manifest.yaml
```

Now deploy the `front` service using Skaffold:

[Terminal 2]
```bash
skaffold dev
```

Observe how Skaffold proceeds to build the container image, and then deploys the service. Once the service is deployed, you'll see the logs of the service in the terminal streaming back to you, the same way you did for the `back` service. Skaffold is also port forwarding the service to your local machine port 8080, so you can test it locally.

Open a browser, and open [http://localhost:8080](http://localhost:8080). You should see the tabs vs spaces voting app, and you should be able to vote for your favorite option. Going from Terminal 1 to Terminal 2, you should the logs for both services and see how the votes are being stored in the database and retrieved from it.

