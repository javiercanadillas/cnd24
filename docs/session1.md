# Lab Session 1 - Containers

## Docker Basics

Using a container, echo "hello-world" (and automatically pull a docker image)

```bash
docker run alpine echo "hello world"
```

Using a contaniner, start a interactive docker session
```bash
docker run -it ubuntu /bin/bash
```

**Question**: What does the `-it` option do? Use Gemini Code Assist to help you out.

**Question**: if you create a file inside the `/root` directory in the container, will it appear in the `/root` folder of your Cloud Shell? Try it. 

Show all docker images available locally

```bash
docker images
```

Run a simple HTTP server with Python in a python:2.7 Docker image
```bash
docker run -d -p 8080:8080 --name webapp python:2.7 python -m SimpleHTTPServer 8080
```

**Question**: What's the `-p` option doing? Why do you think it's necessary? How do you try what this container is doing?

**Question**: This container took more time to pull. How big is it? Can you do better?

See the running docker containers
```bash
docker ps
```

Stop a container
```bash
docker stop webapp
```

Start a container
```bash
docker start webapp
```

Delete a container
```bash
docker rm -f webapp
```

Delete a image
```bash
docker rmi alpine
```

**Question**: This container image couldn't be deleted. Why? Can you remedy the situation so the container image is deleted?

## Building an image

Build a docker image by commit

```bash
docker run -it ubuntu:14.04 /bin/bash
apt update
exit
docker ps -a
docker commit $(docker ps -lq) ubntu:update
docker diff $(docker ps -lq)
```

Build a docker image by export / import tar files
```bash
docker export $(docker ps -lq) > /tmp/update.tar
docker import - update < /tmp/update.tar
```

You're going to containerize now your first Python Flask application. From your terminal, create a new folder to host your python app:

```bash
mkdir $HOME/my-python-app
cd $HOME/my-python-app
```

You can make this new folder as your default workspace in Code OSS by running this from the terminal:

```bash
cloudshell open-workspace $HOME/my-python-app
```

Inside that folder, create a `hello.py` file with the following content:
```python
#!/usr/bin/env python

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
  return 'Hello World!'

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)
```



Also, inside that folder, create a `Dockerfile` with the following content:
```
FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y python python-pip
RUN apt-get clean all
RUN pip install flask

ADD hello.py /tmp/hello.py

EXPOSE 8080

CMD ["python","/tmp/hello.py"]
```

**Question**: Analyze this Dockerfile, can it be improved?

Yes! You can do better than this, try something like the following instead as the content of your `Dockerfile`:

```
FROM python:3.12.3-slim

RUN pip install flask

ADD hello.py /tmp/hello.py

EXPOSE 8080

CMD ["python","/tmp/hello.py"]
```

This image is leaner, has all the tools required by Python, and you don't have to update their packages.

Build a docker image by writing Dockerfile:
```bash
cd $HOME/my-python-app
docker build -t flask .
docker run --name my-web-app -p 8080:8080 -d flask
curl http://localhost:8080/
docker rm -f my-web-app
```

## Inspecting an image locally

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

Get the images you've got so far:

```bash
docker image ls
```

Pick the `IMAGE_ID` from this last image and store it an variable:
```bash
IMG_ID=<IMAGE_ID>
```

Inspect the image to see its layers composition:
```bash
docker image inspect $IMG_ID
```

**Question**: Where's the image?

You can check how the image is hosted in your local Cloud Shell.

List the images in the Filesystem of your machine:

```bash
IMAGE_SHAS=$(sudo ls /var/lib/docker/image/overlay2/imagedb/content/sha256)
echo $IMAGE_SHAS
```

You should get a list of SHA hashes corresponding to the images that you have. You can check that by listing the images and checking that the hashes correspond:
```bash
docker images
```

Now, you're going to pick the first image in the listing and get the contents of the image manifest:

```bash
img_hashes_array=($IMAGE_SHAS)
sudo cat /var/lib/docker/image/overlay2/imagedb/content/sha256/${img_hashes_array[0]} | jq
```

Spend some time looking at this file and trying to figure out the structure of the image according to the previous diagrams.

## Publishing an image

Tag a docker image so it can be pushed to Artifact Registry:
```bash
export REPO_NAME="docker-repo"
gcloud artifacts repositories create $REPO_NAME --location=$REGION --repository-format=docker
```

And finally, build the image. Instead of using the `docker build` command, that does a local build, you're going to use a Cloud Service called [Google Cloud Build]() that's going to upload your code
docker build -t "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/flask-demo:latest" .
#gcloud auth configure-docker $REGION-docker.pkg.dev
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/flask-demo:latest
```

List the images in the remote repository and check that your image is there:
```bash
gcloud artifacts docker images list $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME
```

## ADVANCED - Further image analysis (image tags and image digests)

Let's use the `gcrane` tool to do our analysis using the Docker v2 REST API that Artifact Registry is implementing:

Get the images in the repo:
```bash
IMG_NAME=ubntu
gcrane ls $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME
```

Get the particular
```bash
gcrane ls $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMG_NAME
```

List images in an image:
```bash
export IMG_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMG_NAME:latest"
gcrane export $IMG_URL - | tar -tvf - | less
```

Extract a single file from an image
```bash
gcrane export $IMG_URL - | tar -Oxf - etc/passwd
```

Get the config for an image:
```bash
gcrane config $IMG_URL | jq
```

Get the manifest for an image:
```bash
gcrane manifest $IMG_URL
```

Diff two configs, or two manifests:
```bash
diff <(crane config busybox:1.32 | jq) <(crane config busybox:1.33 | jq)
diff <(crane manifest busybox:1.32 | jq) <(crane manifest busybox:1.33 | jq)
```

Perform an advanced operation, like adding a the contents of a directory to an image:
```bash
NEW_DIR="enhance_img"
cd
mkdir $NEW_DIR
echo "This is a warning text" > "$NEW_DIR/warning.txt"
gcrane append -f <(tar -f - -c ${NEW_DIR}/) -t $IMG_URL
```

