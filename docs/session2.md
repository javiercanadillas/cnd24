# Lab Session 2 - Kubernetes

## The Kubernetes Cluster

Ask Gemini to create a new Google Kubernetes Engine cluster. Use a prompt like this and think why this is a good prompt:

```text
Using gcloud, create a regional, three nodes GKE cluster named `my-cluster` using the shortest command line possible. The region should be `europe-west1`.
```

The proposed command should be something as this:

```bash
gcloud container clusters create my-cluster --num-nodes=3 --region=europe-west1
```

**Question**: What does it mean that you're specifying a region there?

The cluster will take some time to create (**why?**). Once it's ready, you can check the status of the cluster. Ask Gemini to show you how to do it. Try different prompts, one that should work given the previous one is this:

```text
Using gcloud, get the nodes of the cluster
```

The two commands proposed in this case are these:

```bash
# Using the `kubectl` command
gcoud container clusters get-credentials my-cluster --region=europe-west1
kubectl get nodes
```

```bash
# Using the `gcloud` command
gcloud container clusters describe my-cluster --region=europe-west1
```

You can also go to the [Google Cloud Console](https://console.cloud.google.com/kubernetes) and check the status of the cluster there. Make sure that you select the right project.

**Question**: What's the difference between the `kubectl` and `gcloud` commands? Why do you think it's necessary to get the credentials of the cluster before using `kubectl`?


## Deploying an application - Your first pod

You're going to deploy a simple application to the cluster. To continue with the example you started in the previous session, create the same app that you created there and deploy it to the cluster.

The steps you would need to follow are these:

1. Create the app, and the requirements file.

Pytho file, `hello.py`:

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

Requirements file, `requirements.txt`:

```text
flask
gunicorn
```

2. Create a Dockerfile

```yaml
FROM python:3.12.3-slim

WORKDIR /app

ADD . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["gunicorn", "-b", "0.0.0.0:8080", "hello:app"]
```

3. Build the image and push it to Artifact Registry

```bash
gcloud artifacts repositories create my-repo --repository-format=docker --location=europe-west1
```

```bash
gcloud builds submit -t europe-west1-docker.pkg.dev/$PROJECT_ID/my-repo/hello .
```

4. Create a pod manifest and deploy it to the cluster

Try to do steps 1 to 3 by yourself. If you get stuck, ask Gemini for help. Once you have the image in Artifact Registry, ask Gemini to show you how to create the pod manifest and deploy it to the cluster.

**Question**: What's the difference between a pod and a container? Does it matter for this particular example?

**Question**: Given that Kubernetes can inject environment variables into the pods, how would you inject the `PORT` environment variable into the pod?

Ask Gemini to create the pod manifest using a precise prompt. The manifest should look like this, save it as `hello-pod.yaml.template`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hello-pod
  labels:
    app: hello
spec:
  containers:
  - name: hello-container
    image: europe-west1-docker.pkg.dev/$PROJECT_ID/my-repo/hello:latest
    ports:
    - containerPort: 8080
    env:
    - name: PORT
      value: "8080"
```

Once you have the manifest, ask Gemini to deploy it to the cluster. You can check the status of the pod using the following command:

```bash
kubectl get pods
```

You can also check the logs of the pod using the following command:

```bash
kubectl logs hello-pod
```

Finally, you can access the pod using the following command:

```bash
kubectl port-forward hello-pod 8080:8080
```

## Pods or Containers?

Let's do a quick exercise to understand the difference between pods and containers.

Create a pod with two containers. The first container should be an Nginx container that serves a simple HTML page. The second container should be a Debian container that writes the current date to the HTML page every second. Name the file `mc1.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mc1
  labels:
    app: mc1
spec:
  volumes:
  - name: html
    emptyDir: {}
  containers:
  - name: 1st
    image: nginx
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html
  - name: 2nd
    image: debian
    volumeMounts:
    - name: html
      mountPath: /html
    command: ["/bin/sh", "-c"]
    args:
      - while true; do
          date >> /html/index.html;
          sleep 1;
        done
```

Before you create the pod, ask Gemini to explain the manifest to you. Once you understand it, create the pod, but instead of doing it in the `default` namespace, do it in a new namespace named `test` that you need to create first. Ask Gemini to show you how to do it.

Once you have the pod running, ask Gemini to show you how to access the HTML page that the Nginx container is serving. You can do it by port-forwarding the Nginx container to your local machine:
  
```bash
kubectl port-forward mc1 8080:80
```

You can inspect what's happening inside the pod running the `cat` command in both containers:

```bash
kubectl -n test exec -it mc1 -c 1st -- cat /usr/share/nginx/html/index.html
kubectl -n test exec -it mc1 -c 2nd -- cat /html/index.html
```

**Question**: Can you explain what's going on when you access the page?

## Kubernetes resiliency - Deployments

Before moving forward, delete the `hello-pod` pod you created before from the `default` namespace. Ask Gemini to show you how to do it.

Create a new container image for the `hello` app that reads an environment variable called `VERSION` and renders an HTML page saying `Hello world from <version>`, where `<version>` is the value of the environment variable. Build the image and push it to Artifact Registry, tagging this image as `v1` (the tag should be something as `europe-west1-docker.pkg.dev/$PROJECT_ID/my-repo/hello:v1`). Ask Gemini to show you how to do it.

Create a Kubernetes deployment for the `hello` app. The deployment should have the following characteristics:

- It shoud have 3 replicas
- It should use the pod manifest you created before as template
- Remember to use the proper selector to match the labels in the pod manifest

Ask Gemini to show you how to create the deployment. Once you have it, save it as `hello-deployment.yaml`, create it into the `default` namespace, and then check the status of the deployment using the following command:

```bash
kubectl describe deployment hello-deployment
```

List the pods created by the deployment:

```bash
kubectl get pods -l app=hello
```

Now, using the pod name of one of the three pods in the deployment, delete it:

```bash
kubectl delete pod <POD_NAME>
```

Observe how the deployment creates a new pod to replace the one you deleted:

```bash
kubectl get pods -l app=hello
```

**Question:** Can you determine the location of the pods in the cluster? How are they distributed?

### Scaling the application by increasing the replica count

Now, scale up the application up to 5 replicas. Ask Gemini to show you how to do it and redeploy the deployment.

**Question**: Compare the pods of the new deployment and the previous one. What's the difference? Did the deployment create new pods or did it reuse the existing ones?

**Question**: So far, you've been accessing pods using port-forwarding, but this is going straight to the pods. How would you access the application if you have multiple replicas?

## Exposing Kubernetes applications - Services

You're now going to expose the deployment you created in the previous step. Create a service manifest file named `hello-service.yaml`, asking Gemini for help if needed.

Apply the manifest to the cluster and check the status of the service. Ask Gemini to show you how to do it.

**Question**: Could you think of a way to show which node the pods are running when accessing the service? If you modify the app, tag the new container image as `v2`.

## Deployment patterns - a better way to upgrade our app

Now you have a new version of the app, that's reading the `hostname` of the node and rendering an HTML page with it.

Modify the `hello-deployment.yaml.template` file to use the new image (remember, with tag `v2`) and redeploy it. To observe what happens, open a new Terminal in the Cloud Shell Editor (let's call it terminal 2) and run the following command:

```bash
kubectl get pods -l app=hello -w
```

Go back to your original terminal (let's call it terminal 1) and apply the new deployment manifest, observing what happens.

**Question**: What could we do so we deploy a new version of the application in a good way?

Create a blue deployment called`blue-deployment.yaml.template`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-blue-deployment
  labels:
    app: hello
    version: blue
spec:
  replicas: 5
  selector:
    matchLabels:
      app: hello
      version: v1
  template:
    metadata:
      labels:
        app: hello
        version: v1
    spec:
      containers:
      - name: hello-container
        image: europe-west1-docker.pkg.dev/$PROJECT_ID/my-repo/hello:v1
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"
```

Apply it:

```bash
envsubst < hello-deployment.yaml.template | kubectl apply -f -
```

Create a new service pointing to this blue deployment, call in service-blue-green.yaml:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: hello-service
spec:
  type: LoadBalancer
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
  selector:
    app: hello
    version: blue
```

Create a green deployment called`green-deployment.yaml.template`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-green-deployment
  labels:
    app: hello
    version: green
spec:
  replicas: 5
  selector:
    matchLabels:
      app: hello
      version: v2
  template:
    metadata:
      labels:
        app: hello
        version: v2
    spec:
      containers:
      - name: hello-container
        image: europe-west1-docker.pkg.dev/$PROJECT_ID/my-repo/hello:v2
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"
```

Now, observe all the pods:

```bash
kubectl get pods -l app=hello -L version -w
```

Finally, switch the service to the green deployment:

```bash
sed 's/blue/green/' hello-service.yaml.template
envsubst < hello-service.yaml.template | kubectl apply -f -
```

Go to the application endpoint and check the version of the app.
