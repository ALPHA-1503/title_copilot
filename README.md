# Title Copilot - Polarion
The main purpose of this project is to generate titles from work items descriptions from Polarion using Mistral.

This script is a combination of 2 main components for Windows :
- A python script that get and send Polarion work items to a LLM.
- A LLM that can be used to rephrase Titles from work items.

## Installation

The installation is half-manual, half-automated.\
The manual part is the installation of the required software.\
The automated part is the installation of each library, and specific changes done to them.
(You also need a /certif repo in the root path of the project with a ca-certificate for polarion webservice.)

### Required installations
#### Windows
1. Python (3.8+): [Python for Windows](https://www.python.org/downloads/)
   - Make sure to check the box *"Add python.exe to PATH"* during the installation
2. Git, if it isn't already installed, to clone this repository: [Git](https://git-scm.com/downloads)
   - You can click *Next* for each step.
3. **[Optional]** A good terminal to have a more user-friendly experience.
   - You can use the new Windows Terminal for exemple: [Windows Terminal](https://www.microsoft.com/en-us/p/windows-terminal/9n0dx20hk701)
#### Linux
1. Python (3.8+):
   ```bash
   sudo apt-get install python3 python3-venv
   ```
2. Git, if it isn't already installed, to clone this repository: 
   ```bash
   sudo apt-get install git
   ```
# Requirements
1. Python, minimum version 3.8.10
    - Make sure to check the box "Add python.exe to PATH" during the installation.
2. Git, to cline this repository: Git
    - You can click Next for each step


### Activate and fill your environment *(Important steps)*
Using a virtual environment is a good practice to avoid conflicts between libraries and versions. And also to keep your main Python installation clean.
#### Windows
1. Find a suitable location for the repository
   ```bash
   cd <DIRECTORY>
   ```
2. Create and activate the virtual environment
   ```bash
   py -m venv .venv
   .\.venv\Scripts\activate
   ```
   If you run into an error with execution policy, check your own execution policy with:
   ```bash
    Get-ExecutionPolicy
   ```
   remember it if you want to put it back later. Then, change it to RemoteSigned and try to activate the environment again:
   ```bash
    Set-ExecutionPolicy RemoteSigned
   ```
3. Clone the repository
   ```bash
   git clone https://gitlab.sw.goiba.net/req-test-tools/polarion-copilot/title_copilot.git
   cd title_copilot
   ```
4. Install the required libraries
   ```bash
   pip install -r requirements.txt
   ```
#### Linux 
1. Find a suitable location for the repository
   ```bash
   cd /your/directory/
   ```
2. Clone the repository
   ```bash
   git clone https://gitlab.sw.goiba.net/req-test-tools/polarion-copilot/title_copilot.git
   cd title_copilot
   ```


#### Before any further steps, you need to fill the environment variables in the .env file.
1. Fill the .env file with the following content, each value must be between quotes "" (the .env file is located at the 
   root path of the project) :
   ```bash
   base_url=<URL> # The URL of your Polarion server (e.g. https://polarion.example.com/polarion)
   openai_api=<URL> # The URL of your OpenAI like API (has to finish with "/v1")
   # It depends on which server you want to modify work items titles.
   polarion_url_dev=<URL> 
   polarion_user=<USERNAME> # The username to access the Polarion server
   polarion_password=<PASSWORD> # The password to access the Polarion server
   polarion_token=<TOKEN> # The user token to access the Polarion server
   ```
   Replace `<URL>`, `<USERNAME>`, and `<TOKEN>` with your own values.
   .env file contains sensitive information, make sure to not share it.

### Tensordock virtual machine

   1. Open [TensorDock](https://dashboard.tensordock.com/deploy)
   2. Get a GPU with at least 48Gb of VRAM
   3. 1GPU, 8Gb of RAM, 2CPU and 30Gb SSD
   4. Select one of the available locations
   5. Choose Ubuntu as operating system
   6. Put a password and a machine name
   7. Deploy
   8. SSH into the machine :
      ```bash
      ssh -p xxxxx user@host -L 22027:localhost:8080 -L 22028:localhost:8000
      ```
9. Run the two docker images :
   ```bash
   docker run -d --gpus all -v ~/.cache/huggingface:/root/.cache/huggingface --env "HUGGING_FACE_HUB_TOKEN=<secret>" -p 8000:8000 --ipc=host vllm/vllm-openai:latest --model mistralai/Mistral-7B-Instruct-v0.2 --max-model-len 2048
   ```
   ```bash
   docker run -d --gpus all -p 8080:80 -v $PWD/data:/data --pull always ghcr.io/huggingface/text-embeddings-inference:1.2 --model-id intfloat/multilingual-e5-large-instruct
   ```
10. Create a ssh key (without password)
   ```bash
   ssh-keygen -t rsa -b 4096
   ```
11. Copy/Paste the pub key in [TensorDock SSH](https://dashboard.tensordock.com/api#:~:text=Create%20Authorization-,SSH%20Public%20Keys,-New)
   
12. Add the private key to your ssh agent
   ```bash
   ssh-add ~/.ssh/id_rsa_tensordock
   ```
We use an SSH key to automatically establish an SSH tunnel to the remote server without needing to enter a password.

### Setup a Linux daemon for automatic containers start. 
Warning: You must have created the container by pulling the images on point 9.
When the two images are booted up, you can proceed.

1. Create a new file in /etc/systemd/system/ :
   ```bash
   sudo nano /etc/systemd/system/containers.service
   ```
2. Fill the file with the following content :
   ```bash
   [Unit]
   Description=Starts all containers service
   After=network.target
   Requires=docker.service
   
   [Service]
   Type=oneshot
   ExecStart=/bin/sh -c '/usr/bin/docker start $(/usr/bin/docker ps -aq)'
   ExecStop=/bin/sh -c '/usr/bin/docker stop $(/usr/bin/docker ps -aq)'
   RemainAfterExit=true
   
3. Reload the daemon and start the service :
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start containers
   
4. Now you can restart the virtual machine without having to restart the containers manually.

### Use the Code
1. Run the launcher for title copilot
   ```bash
   py run_app.py
   ```
2. Enjoy the ride!

   

