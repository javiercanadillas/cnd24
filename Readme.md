# Cloud Native Development Labs '24

This is the lab content repository for the Cloud Native Development (with Python and Cloud Run) class '24. The following instructions and modules assume you're using a Qwiklabs environment. Make sure you ask your instructor for specific instructions on how to access it.

## Basic Setup

Open a new [Google Cloud Shell Editor](https://ide.cloud.google.com) in your Qwiklabs project. Once there:

1. click on "Cloud Code: Sign-in" in the left part of the bar that appears at the bottom of the IDE. Click Authorize if requested.
2. Open a new integrated terminal pane going to "Terminal > New Terminal" or pressing ``CTRL + ALT + ` `` (or ``CTRL + OPTION + ` `` if you're on a Mac).

In the terminal, set up your project, the labs will be assuming `europe-west1` as region:

```bash
export PROJECT_ID=<your qwiklabs project ID here>
```

Then, run the following Cloud Shell configuration script to get everything setup:

```bash
CS_SOURCE="https://raw.githubusercontent.com/javiercanadillas/qwiklabs-cloudshell-setup/${GIT_BRANCH:-main}/setup_qw_cs"
bash <(curl -s "$CS_SOURCE") && exec $SHELL -l
```

This configures a sane prompt that will give you hints on things like Python virtual environments or git status, some additional CLI tools, Code OSS behavior, and Gemini Code Assist.

For changes to be effective, you need to source the new `.bashrc` configuration:

```bash
source ~/.bashrc
```

## Labs

### Module 1 - Containers and images
- Basic: [Understanding container images](docs/session1.md)
- Homework: [Practicing with the Ngnix Docker Image](https://www.docker.com/blog/how-to-use-the-official-nginx-docker-image/)
- Extra & optional: [Can you get Doom to work as a container from the browser?](https://shipyard.build/blog/doom-in-your-app-with-docker-compose-and-shipyard/)

### Module 2 - Kubernetes
- Basic: [Understanding Kubernetes](docs/session2.md)