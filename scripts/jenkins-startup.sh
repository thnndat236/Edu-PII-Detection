#!/bin/bash

# --------------------------------------------
# Install Docker
# --------------------------------------------
echo "Installing Docker..." >> /var/log/startup-script.log
sudo apt-get update
sudo apt-get install -y docker.io

# --------------------------------------------
# Install Jenkins
# --------------------------------------------
echo "Installing Jenkins..." >> /var/log/startup-script.log
sudo apt update
sudo apt install -y openjdk-17-jdk curl gnupg2

# Add the official Jenkins GPG key to authenticate packages from the repository
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null

# Add the official Jenkins Debian repository to the source list
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# Installs Jenkins from the newly added repository
sudo apt update
sudo apt install -y jenkins

# Enables and starts the Jenkins service
sudo systemctl enable jenkins
sudo systemctl restart jenkins

# Grants the Jenkins user permission to run Docker commands
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins

# --------------------------------------------
# Install Google Cloud SDK and GKE Auth Plugin
# --------------------------------------------
echo "Installing Google Cloud SDK..." >> /var/log/startup-script.log
# Installs the Google Cloud SDK to manage Google Cloud resource, including GKE
curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts

# Adds the Google Cloud SDK to PATH for gcloud command usage
echo 'source "$HOME/google-cloud-sdk/path.bash.inc"' >> ~/.bashrc
source "$HOME/google-cloud-sdk/path.bash.inc"

# Installs GKE Auth plugin for authentication with GKE
sudo apt-get update
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o \
  /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a \
  /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get update
sudo apt-get install google-cloud-sdk-gke-gcloud-auth-plugin -y

sudo bash -c "echo 'GKE Auth plugin installed: $(gke-gcloud-auth-plugin --version)' >> /var/log/startup-script.log"

# --------------------------------------------
# Install kubectl
# --------------------------------------------
echo "Installing kubectl..." >> /var/log/startup-script.log
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl

# --------------------------------------------
# Install Helm (https://helm.sh/docs/intro/install/)
# --------------------------------------------
echo "Installing Helm..." >> /var/log/startup-script.log
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh >> /var/log/startup-script.log 2>&1

# --------------------------------------------
# Log completion
# --------------------------------------------
echo "Startup script completed successfully" >> /var/log/startup-script.log