# Connecting to Cloud SQL from Cloud Run

Connecting to databases is one of the most common operations to be done when developing Cloud Nativa applications. This is like so because serverless platforms like Cloud Run rely on them to persist data due to the very stateless nature of these platforms.

In this mode, you'll learn how to connect to one of the most common types of Databases in real life companies.

## Bootstrapping this module

This module builds on the work done in [Module 2](../module1/Module2.md).

If you have just finished Module 2 without stopping your Qwiklabs lab, there's nothing additional for you to do in this section and you should continue to [Creating a Cloud SQL Postgre Database](creating-a-cloud-sql-postgre-database) section below.

However, **if you're starting fresh from a new Qwiklabs lab** because you did Module 2 some day in the past, you need to do the following steps to automatically replay the steps done in Module 2.

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
4. Run Module 2 steps replay script:
  ```bash
  cd "$HOME/cnd/assets/module2" && ./module2_replay_steps.bash
  ``` 
5. As requested in the output of the previous script, source your `.bashrc` file
  ```bash
  source "$HOME/.bashrc"
  ```

Once all this has been done, you should be ready to continue with Module 3. Read on.

## Creating a Cloud SQL Postgre Database

### Creating the infrastructure

The first thing to do is to create the necessary Cloud Infrastructure, starting with the Cloud SQL Postgre instance and database. Cloud SQL offers you some other options (MySQL and SQLServer), but PosgreSQL seems to be an option that's widely used nowadays.

Connect to your Cloud Shell environment and enable the Cloud SQL Admin API:
```bash
gcloud services enable sqladmin.googleapis.com
```

Then, set the SQL database connection variables that the next steps will be using and persist them into a file:

```bash
mkdir -p $HOME/cnd/db-api/src
cd $HOME/cnd/db-api
cat ../assets/module3/labven_extra >> .labenv_db
```

It's a good idea to have a look at what you've added to your shell to understand what you're doing before applying the changes:
```bash
bat .labenv_db
```

Notice how you're setting the variables to create and establish the database connection. You'll be using these variables in the next steps.

Now, make the changes effective:
```bash
source ./.labenv_db
```

Create a new Cloud SQL - PostgreSQL database instance using `gcloud` and selecting the `db-g1-small` machine type to reduce costs:
```bash
gcloud sql instances create "$DB_INSTANCE" \
  --tier=db-g1-small \
  --region="$REGION" \
  --database-version=POSTGRES_14
```

Store the instance IP address in an environment variable and persist it into the environment file that you created before:
```bash
echo "
declare -x SQL_IP="$(gcloud sql instances describe "$DB_INSTANCE" --format="value(ipAddresses[0].ipAddress)")"
" >> .labenv_db
source ./.labenv_db
```

Set the password for the default user in the database:
```bash
echo $DB_PASS
gcloud sql users set-password postgres \
  --instance=$DB_INSTANCE\
  --password=$DB_PASS
```

Create a new database in the database instance you've just created:
```bash
gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE
```

You now have all the infrastructure you need.

### Creating the database
You'll now create a new structure for a new Cloud Run service that you will be developing. This new service will be called `db-api`, and will wrap our application specific database operations through an API built with Flask.

Create a new folder structure for your code, and a new python environment inside it:
```bash
cd $HOME/cnd/db-api
python -m venv .venv
source .venv/bin/activate
```

Note how you enabled the virtual environment, so any Python package management is done inside it.

You will now uuse `pip-tools` for a saner dependency management:
```bash
cd $HOME/cnd/db-api
pip install pip-tools
cp $HOME/cnd/assets/module3/requirements-local.in ./requirements-local.in
pip-compile ./requirements-local.in
pip-sync requirements-local.txt
```

This just took a simple `requirements-local.in` requirements file that only has the two required dependencies for now, defined in an explicit way, and generates a `requirements.txt` file with all the subdependencies, adding comments to track which dependencies are coming from which. The last `pip-sync` is just making sure that the `requirements.txt` file is processed by pip and that everything is consistent.

You'll now use a Python program called `create_db.py` to create the database structure. This file contains code to create a table with data into the database you created previously that's ready for the API you're about to develop and deploy.

```bash
cd $HOME/cnd/assets/module3
python create_db.py
```

Observe how a new table is created in the database and the entries are logged back by the program to your console. **It's a good idea to have a look at the code to understand what it's doing.**

You can also test the database connection with another Python program called `test_db.py` at any time during this module:
```bash
cd $HOME/cnd/assets/module3
python test_db.py
```

If you do so now just after creating the database table, you should see one entry in the database.

This all works as is from Cloud Shell without requiring further authentication configuration in the code because the code is using Google Cloud SDK's [Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc).

## Creating the application

You'll now move to the `src` folder and create a new Flask application that will wrap a couple of database operations in a simple API.

```bas
cd $HOME/cnd/db-api/src
```

From there, you'll copy the relevant files from the assets folder:
```bash
cp $HOME/cnd/assets/module3/{connect_connector.py,app.py,base_logger.py} .
```

You'll also copy the application frontend files that you'll be using later, they're Flask templates:
```bash
cp -r $HOME/cnd/assets/module3/templates .
```

Explore the the source code that you just copied to understand how the application is structured. You'll see that the `app.py` file contains the Flask application, and that it's using the `connect_connector.py` file to connect to the database and perform the operations. The `base_logger.py` file is just a helper to log messages to the console. The `templates` folder contains the frontend files that allow you to vote for TABS or SPACES, submits a POST request to the API and queries the API with a GET request to show the results.

### Running the application locally

You'll now run the application locally to test it. You'll need to set the environment variables that the application will be using to connect to the database. You'll do so by sourcing the `.labenv_db` file that you created before if you haven't done it already:
```bash
source $HOME/cnd/db-api/.labenv_db
```

Then, run the application:
```bash
cd $HOME/cnd/db-api/src
python app.py
```

You should see the application outputting the URL where it's running, and also some logs in the console. Open that URL in a new tab in your browser and you should see the frontend of the application. You can vote for TABS or SPACES and see the results.

You can also test the API directly with `curl`, opening a new tab in Cloud Shell and running the following command:
```bash
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -d 'team=TABS' localhost:8080/votes
```

## Create a Cloud Run Flask-based API

You'll now create a new Cloud Run service to be able to deploy your app in the cloud.

First, copy the Dockerfile and the requirements file from the assets folder:
```bash
cp -- $HOME/cnd/assets/module3/{Dockerfile,.dockerignore,requirements.in} .
```

Then, from the `requirements.in` file, generate the `requirements.txt` file that will be used by the Dockerfile for the production service:
```bash
pip-compile requirements.in
```

You can now build the container, push it to Artifact Registry and deploy it to Cloud Run in one single step:
```bash
cd $HOME/cnd/db-api
gcloud run deploy db-api \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars=INSTANCE_CONNECTION_NAME="$PROJECT_ID:$REGION:$DB_INSTANCE" \
  --set-env-vars=DB_NAME="$DB_NAME" \
  --set-env-vars=DB_USER="$DB_USER" \
  --set-env-vars=DB_PASS="$DB_PASS"
```

There are several problems with the way you're deploying this. To start with, the application has a UI that's not decoupled from the component performing database operations, and that has forced you to deploy the application without authentication. Also, the application is managing connection secrets to the database using environment variables in the clear, which is far from ideal.

You'll fix the first issue by creating a new service that will act as a proxy to the database, and that will be the only component that will be allowed to connect to the database. The application will then connect to this new service instead of connecting directly to the database. Once that is fixed, you'll fix the second issue by using Secret Manager to store the database credentials. You'll see all that in the next module.