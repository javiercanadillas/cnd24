
# Developing using VSCode Remote Server against Cloud Shell

Install the Google Cloud SDK in your local machine. Instructions depend on your laptop Operating System platform, so it's better to point you to the [official instructions to get them installed](https://cloud.google.com/sdk/docs/install#windows).

For Mac OS X though, I'd strongly recommend you to [install Homebrew in your machine](https://docs.brew.sh/Installation), and then use to install any kind of software really. With it, you can install the Google Cloud SDK with a single command:

```bash
brew install --cask google-cloud-sdk
```

## Installing VSCode

There's Vim, there's Emacs... there are plenty of good code editors out there. But one that's very popular lately is VSCode. This tutorial will focus on it because it's very similar in developing experience to the one you get when you use the [Cloud Shell Editor](https://cloud.google.com/shell/docs/editor-overview).

Again, because your OS may be different than mine, the best pointer to install VSCode in your machine is the [official installation docs](https://code.visualstudio.com/download).

If you happen to be on Mac OSX, using Homebrew is just one liner:

```bash
brew install visual-studio-code
```

Just as an example of some customization to your local VSCode, if you're doing Python development in the Cloud I'd recommend you to install several useful plugins from the VSCode Marketplace:

- Docker (from Microsoft)
- Python (from Microsoft)
- Ruff - a very fast Python linter
- Cloud Code (from Google) - A extension to integrate your vscode environment with Google Cloud services.

## Setting up local connection to remote Cloud Shell

OK, you have the Google Cloud SDK installed in your computer. Now what? It's time to learn how to se up your local vscode so you get Cloud Shell Terminal and Cloud Shell files into it in an integrated way.

The first thing you need to do is to authenticate from your loca Google Cloud SDK using your GCP credentials. You do this by using `gcloud auth`:
```bash
gcloud auth
```

This will open a browser page and will ask you to use your GCP username and password. **Important**: if you're doing this from Qwiklabs, before running `gcloud auth` first open an incognito window and the run the command. This way, the request to enter the credentials will open in the incognito window instead of any other browser or browser profile you may have open.

Once authenticated, select the project you'll be working with using `gcloud`:
```bash
gcloud config set project <your-project-id>
```

Now, you're ready to start configuring the remote access itself. Open a terminal in your laptop and type the following command:

```bash
gcloud cloud shell ssh --dry-run --authorize-session
```

This outputs the command that `gcloud` would use if you were to connect through SSH from your local terminal to Cloud Shell, but does not actually establishes the connection. This allows you to see the Cloud Shell VM IP, that you will need to use to connect to it from vscode.

The output will look like this:
```bash
Pushing your public key to Cloud Shell...done.                                                                                                             
Starting your Cloud Shell machine...
Waiting for your Cloud Shell machine to start...done.                                                                                                      
/usr/local/bin/ssh -t -p 6000 -i /Users/javiercm/.ssh/google_compute_engine -o StrictHostKeyChecking=no student_04_937de7a5d015@34.78.115.74 -- DEVSHELL_PROJECT_ID=qwiklabs-gcp-04-79b33b3599d5 'bash -l'
```

So, from the command output, copy and paste the VM IP that's there (in this example, it is **`34.78.115.74`** but yours will be different). You will use it when connecting from vscode.

Open VScode, press `Cmd + Shift + P` (or `Ctrl + Shift + P` if you're in Windows or Linux), and type/select "Remote-SSH: Connect to Host..." in the window that appears there:

![Connect to host](./Remote_Connect_to_host.png)

Then, type `Configure ssh hosts...` in the box that appears:

![Configure ssh host](./Configure_ssh_host.png)

and then, select the SSH configuration file to update (VSCode should offer you the default one that makes most sense for your OS):

![Select ssh configuration file](./Select_ssh_file.png)

The corresponding ssh config file will open (this file is typically located in the ~/.ssh folder if you're using a Linux or Mac computer). At the end of that file, add the following lines:

```text
Host myremote
  HostName 34.78.115.74
  Port 6000
  ForwardAgent yes
  User student_04_937de7a5d015
  IdentityFile ~/.ssh/google_compute_engine
```

Make sure the `HostName` and `User` directives match the information from your GCP user id and Cloud Shell VM IP.

Now, you should be able to connect to Cloud Shell. Use `Cmd +  Shift + P` (or `Ctrl + Shift + P`) again in VSCode and type/select the option "Remote-SSH: Connect to Host...". It will show you a list of hosts to connect to, and you should see the one you just added, that's called `myremote` in this example.

Select it and VSCode should open a new window. In that new window you're now in whatever you're doing, you're doing in the Remote Cloud Shell (both opening files and opening terminals will happen remotely in Cloud Shell).