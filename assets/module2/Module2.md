# Module 2 - Packaging into a container image and deploying into Cloud Run

## Bootstrapping this module

This module builds on the work done in [Module 1](../module1/Module1.md).

If you have just finished Module 1 without stopping your Qwiklabs lab, there's nothing additional for you to do in this section and you should continue to [Packaging the application into a container image](packaging_the_application_into_a_container_image) section below.

However, **if you're starting fresh from a new Qwiklabs lab** because you did Module 1 some day in the past, you need to do the following steps to automatically replay the steps done in Module 1.

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
4. Run Module 1 steps replay script:
  ```bash
  cd "$HOME/cnd/assets/module1" && ./module1_replay_steps.bash
  ``` 
5. As requested in the output of the previous script, source your `.bashrc` file
  ```bash
  source "$HOME/.bashrc"
  ```

Once all this has been done, you should be ready to continue with Module 2. Read on.

## Packaging the application into a container image

You will now create the necessary Dockerfile specifying how the container image should be built. 

Copy the following Dockerfile into your application directory:
```bash
cp $WORKDIR/assets/module2/Dockerfile $WORKDIR/myfirstapp
```

Open the dockerfile in the Cloud Shell Editor:
```bash
cloudshell edit $WORKDIR/myfirstapp/Dockerfile
```

The file should look like this:
```Dockerfile
# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY ./src ./
COPY requirements.txt ./

# Install production dependencies.
RUN pip install \
  --no-cache-dir \
  --disable-pip-version-check \
  --root-user-action=ignore \
  -r requirements.txt
RUN pip install gunicorn

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
```

As you'll be using Gunicorn, you'll also need the dependency, but instead of adding it to your requirements file, it's something that's explicitly set in the Dockerfile.
```

**Discussion: what's a container image? What's a Dockerfile useful for?**

Now, add the following `.dockerignore` file as to not include unnecessary clutter into your container image:
```bash
cp $WORKDIR/assets/module2/.dockerignore $WORKDIR/myfirstapp
```

The file should look like this:
```text
Dockerfile
README.md
**/*.pyc
**/*.pyo
**/*.pyd
**/__pycache__
**/.pytest_cache
```

### Building and publishing a container image with Docker

Build your image tagging using Docker. Tag it with the proper Artifact Registry ID (it should follow the convention `LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY/IMAGE`):
```bash
docker build -t "$REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/myfirstapp" .
```

**Discussion: what's the meaning of the -t option used above?**

Check that you've got the image locally:
```bash
docker image ls
```

Inspect the image to see its layers composition:
```bash
docker image inspect $(docker image ls --quiet)
```

Where's the image? You can check how the image is hosted in your local Cloud Shell:
```bash
IMAGE_SHA=$(sudo ls /var/lib/docker/image/overlay2/imagedb/content/sha256)
echo $IMAGE_SHA
sudo cat /var/lib/docker/image/overlay2/imagedb/content/sha256/$IMAGE_SHA | jq
```

Run the container locally:
```bash
docker run -e PORT=8080 -p 8080:8080 $REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/myfirstapp
```

Inspect that the application is running correctly and once done, press `Ctrl+C` to stop the container.

### Pushing the image to a remote registry

You'll now push the image to a remote registry where Cloud Run can pull the image from.

The first thing you'll need is a Docker Artifact Registry repository where to push your image:
```bash
# Enable Artifact Registry repository
gcloud services enable artifactregistry.googleapis.com
# Create the repository
gcloud artifacts repositories create docker-main --location=$REGION --repository-format=docker
# List the recentlly created repository
gcloud artifacts repositories list
```

For the docker daemon to be able to push images to a remote registry, you'll need to authenticate and authorize. This means configuring Docker so it has the right credentials to push images to the Artifact Registry docker registry that you created in the steps above:
```bash
gcloud auth configure-docker $REGION-docker.pkg.dev
docker push $REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/myfirstapp
```

When asked, answer yes.

List the images in the remote repository and check that your image is there:
```bash
gcloud artifacts docker images list $REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy
```

### Image tags and image digests

(This section is based on the more detailed article [Using container image digests](https://cloud.google.com/kubernetes-engine/docs/archive/using-container-images))

When working with container images, image tags are a common way of referring to different revisions of an image. Something that is typically done is to tag images with a version identifier at build time, like v1.1.

Tags make image revisions easy to manage by using human-readable identifiers. However, tags are mutable references, which means the image referenced by a tag can change, as illustrated in the following diagram:

<p align="center">
  <img width="460" height="300" src="https://cloud.google.com/static/architecture/images/using-container-images-1-tags.svg">
</p>

To understand how the tags and digests are used, it's better to visualize the overall components of a container image:

<p align="center">
  <img width="460" height="300" src="https://cloud.google.com/static/architecture/images/using-container-images-2-structure.svg">
</p>

Let's pull all the information from the published image using the Docker v2 REST API that Artifact Registry is implementing:

```bash
# Gets the image digest from the Artifact Registry repository
IMAGE_DIGEST="$(gcloud artifacts docker images describe \
    $REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/myfirstapp:latest \
    --format 'value(image_summary.digest)')"
# Gets a list of tags for the image
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" https://$REGION-docker.pkg.dev/v2/$PROJECT_ID/cloud-run-source-deploy/myfirstapp/tags/list
# Gets the image manifest
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" https://$REGION-docker.pkg.dev/v2/$PROJECT_ID/cloud-run-source-deploy/myfirstapp/manifests/$IMAGE_DIGEST | less
```

What's important from all this is that to deploy container images in a reliable way (a software delivery pipeline, actually) it is best to rely on image digests instead of image tags. You'll be working however with both indistinctively during these modules as not not overcomplicate your practice.

### Deploying the image on Cloud Run

Finally, use the Google Cloud SDK to tell Cloud Run to fetch the image from the Artifact Registry repo and deploy it:
```bash
# You also need to enable the Cloud Run Service in your GCP project:
gcloud services enable run.googleapis.com
# And then deploy the app
gcloud run deploy myfirstapp \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/myfirstapp" \
  --allow-unauthenticated \
  --set-env-vars="NAME=CND"
```

As this is the first time you're deploying an app on Cloud Run, it will take a bit of time while the service is being activated.

**Discussion: what's happening when you use the `--set-env-vars` option with the `gcloud` command?**

**Discussion: how can you test the app now?**

### Building and publishing a container with Cloud Build

You don't have to use any local tooling to build images, Cloud Build can do that for you.

You'll now rebuild the container image from the Dockerfile specification using the Docker Cloud Build builder and the Google Cloud SDK:

```bash
cd $WORKDIR
gcloud builds submit -t $REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/myfirstapp .
```

Note how here, instead of creating an image locally and uploading it to Artifact Registry, Cloud Build is zipping the source code and uploading it to the Cloud. Cloud Build will get it in a Google Cloud Storage bucket and will proceed to build an image from it.

You can now deploy this image version using `gcloud`:
```bash
gcloud run deploy myfirstapp \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/myfirstapp" \
  --allow-unauthenticated \
  --set-env-vars="NAME=CND"
```

Get the service URL so you can test it:
```bash
gcloud run services describe myfirstapp
```

### Further automating the build and deploy process with the Google Cloud SDK

The Google Cloud SDK includes tooling so you don't even have to explicitly do the container image building. Run the following command and observe what's happening:

```bash
cd $WORKDIR
gcloud run deploy myfirstapp \
  --source . \ 
  --allow-unauthenticated \
  --set-env-vars="NAME=CND"
```

### Using Cloud Run's service manifest

Cloud Run is compatible with Knative. This means you can use a manifest file to define your service.

Inspect the file in `$WORKDIR/assets/module2/cloudrun-manifests/myfirstapp-cloudrun-service.yaml`, that looks like this:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: myfirstapp
  labels:
    cloud.googleapis.com/location: $REGION
spec:
  template:
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: $REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/myfirstapp
        ports:
        - name: http1
          containerPort: 8080
        env:
        - name: NAME
          value: MSBC
        resources:
          limits:
            memory: 512Mi
            cpu: 1000m
  traffic:
  - percent: 100
    latestRevision: true
```

Modify the file so it reflects the proper environment variables and place it into your application directory:
```bash
mkdir -p "$WORKDIR/myfirstapp/cloudrun-manifests"
envsubst < "$WORKDIR/assets/module2/cloudrun-manifests/myfirstapp-cloudrun-service.yaml" > "$WORKDIR/myfirstapp/cloudrun-manifests/myfirstapp-cloudrun-service.yaml"
```

Then, deploy the service using the manifest file:
```bash
gcloud run services update myfirstapp
```
