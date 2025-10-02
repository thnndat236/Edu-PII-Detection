# Edu-PII-Detection

## 1. Infrastructure Setup Guide

This guide provides the detailed, one-time commands required to provision the project's cloud infrastructure on Google Kubernetes Engine

---

### A Closer Look at Our Cloud Foundation
At the heart of this project lies a carefully crafted infrastructure, defined declaratively using Terraform in the `terraform/` directory. This approach ensures that our setup is reproducible, version-controlled, and easy to manage. Our cloud environment consists of two primary actors working in concert: a powerful Google Kubernetes Engine (GKE) cluster to run our application and a dedicated Jenkins VM to oschestrate our continue integration and continue deployment (CI/CD) pipeline. 

#### The Workhorse: Google Kubernetes Engine (GKE) Cluster

The GKE cluster, named `{project-id}-gke` is the stage where our Education PII Detection API performs. It's a GKE Standard cluster, which provides us with granular control over its configuration, allowing us to fine-tune the environment to meet the specific demands of our workloads.
- **Cluster Configuration**: The cluster is provisioned in `asia-southeast1` region with a single node to start, built on an `e2-standard-2` machine type. This offers a balanced blends of computing power and cost-efficiency, perfect for our development and deployment needs.
- **Scalability**: While we start with one node, the power of GKE lies in its ability to scale effortlessly as our application's traffic and complexity grow.

#### The Conductor: The Jenkins CI/CD Server

Automation is key to modern software development. Our CI/CD pipeline is driven by `{project-id}-jenkins` Google Compute Engine instance, a virtual machine dedicated to building, testing, and deploying our application.
- **Self-Configuring VM**: The VM provisions itself with `jenkins-startup.sh` upon creation. It install everything needed to get the job done:
    - Docker: To create and manage containerized environments for our builds.
    - Jenkins: The core of our automation server.
    - Google Cloud SDK and GKE Auth Plugin: To authenticate and interact with other Google Cloud services securely.
    - Kubectl & Helm: The essential tool for communicating with our GKE cluster and deploying our application using Helm charts.
- **Secure Accessibility**: A specific firewall rule, `jenkins-firewall`, is created alongside the instance. It selectively opens ports like `8080` for the Jenkins web UI and `22` for SSH access, ensuring the server is both accessible for us and secure from unwanted traffic..

Together, these resources, oschestrated by a few simple Terraform commands, from a robust, automated, scalable foundation for the Education PII Detection API. 

---
### 1.1. Provision GCP Resources with Terraform

These steps use Terraform to declaratively create the GKE cluster and the Jenkins VM as defined in the `terraform/` directory. This approach ensures our infrastructure is reproducible and version-controlled.

1. **Navigate to the Infrastructure Directory**:

```bash
cd terraform/
```

2. **Initialize Terraform**:

This downloads the required GCP provider plugins and prepares the workspace.

```bash
terraform init
```

3. **Review and apply the plan**:

```bash
# Show a "dry run" of the resources to be created
terraform plan

# Execute the plan
terraform apply
```
This process can take several minutes as it waits for GCP to create the GKE cluster and the compute engine.

### 1.2. Verify Infrastructure Health

After Terraform completes, it's crucial to verify that all resources were created successfully and are accessible.

1. **Check the GKE cluster**:

Verify that the GKE cluster is running and in a `RUNNING` state.

```bash
gcloud container clusters list
```

2. **Check the Jenkins VM Instance**:

Verify that the `{project-id}-jenkins` compute instance is also `RUNNING`.

```bash
gcloud compute instances list
```
3. **Check the Firewall Rules**:

Ensure the firewall rules `jenkins-firewall` was created to allow traffic on the necessary ports.

```bash
gcloud compute firewall-rules list
```

4. **Connect kubectl the New Cluster**:

This command updates your local `kubeconfig` file with the credentials and endpoint for your new GKE cluster, allowing you to interact with it.

```bash
gcloud container clusters get-credentials {project-id}-gke --region asia-southeast1
```

5. **Verify Cluster Connectivity**:

A successful response to this command confirms you have authenticated to the cluster and have basic permissions.

```bash
kubectl get nodes
```

You should see the nodes that make up your GKE cluster.

6. **Check Kubernetes context and change the context**:

```bash
kubectl config get-contexts
kubectx
```

### 1.3. Post-Provisioning Steps

- **Create the Namespace**: Your Helm chart deploys to the `model-serving` namespace. You can create it ahead of time.

```bash
kubectl create namespace model-serving
```

- **Restart the Instance (If needed)**: If the startup script for the Jenkins VM fails for any reason, you can trigger it to run again by resetting the instance.

```bash
gcloud compute instances reset {project-id}-jenkins --zone asia-southeast1-a
```

- **Watch Startup Logs**: To debug the Jenkins VM startup script, you can tail the serial port output.

```bash
gcloud compute instances get-serial-port-output {project-id}-jenkins --zone asia-southeast1-a --port 1
```



## Step-by-step to deploy on GKE manually

**Step 1**: Deploy `ingress-nginx` first and copy external-ip for later application and monitoring deploying:

```bash
# Create namespace and install ingress-nginx
./scripts/ingress-nginx.sh install

# Check external IP of ingress-nginx-controller service
./scripts/ingress-nginx.sh check-ip
```

Explore `ingress-nginx-setting.md` for more information: [ingress-nginx-setting.md](helm-charts/ingress-nginx/ingress-nginx-setting.md)

**Step 2**: Deploy `ELK Stack` for logging on GKE:

```bash
# Create namespace logging and install Elk Stack (Elasticsearch, Filebeat, Logstash, Kibana)
./scripts/elk.sh install

# Get Elasticsearch credentials for Kibana login
./scripts/elk.sh get-credentials
```

Access Kibana on `kibana.<EXTERNAL_IP>.sslip.io`

Explore `elk-setting.md` for more information: [elk-setting.md](helm-charts/elk-stack/elk-setting.md)

**Step 3**: Deploy `Jaeger` for tracing on GKE:

```bash
# Create namespace tracing and copy Elasticsearch credentials from logging to tracing namespace
./scripts/jaeger.sh copy-credentials
 
# Install Jaeger
./scripts/jaeger.sh install

# Verify Elasticsearch connectivity
./scripts/jaeger.sh verify
```

Access Jaeger on `jaeger.<EXTERNAL_IP>.sslip.io`

Explore `jaeger-setting.md` for more information: [jaeger-setting.md](helm-charts/jaeger/jaeger-setting.md)


**Step 4**: Deploy `kube-prometheus-stack` for metrics on GKE:

```bash
# Create namespace monitoring and install kube-prometheus-stack
./scripts/prometheus.sh install
 
# Get access kube-prometheus-stack-grafana credentials
./scripts/prometheus.sh get-credentials
```

Access Prometheus on `prometheus.<EXTERNAL_IP>.sslip.io`
Access Grafana on `grafana.<EXTERNAL_IP>.sslip.io`
Access Alertmanager on `alertmanager.<EXTERNAL_IP>.sslip.io`

Explore `prometheus-setting.md` for more information: [prometheus-setting.md](helm-charts/kube-prometheus-stack/prometheus-setting.md)


## Building a Docker Image manually

1. Build the Docker Image based on instructions in the `Dockerfile`:

```bash
# Build image with tag
docker build -t qdawwn/edu-pii-detection:v1.0 .
```

2. Tag and Push the Image to Docker Hub:

```bash
# Tag image as latest image
docker tag qdawwn/edu-pii-detection:v1.0 qdawwn/edu-pii-detection:latest

# Login to Docker
docker login

# Push image
docker push qdawwn/edu-pii-detection:v1.0
docker push qdawwn/edu-pii-detection:latest
```

## Create namespace `model-serving` and deploy application on GKE

```bash
kubectl create namespace model-serving

kubectl get po -n model-serving -w

helm upgrade --install edu-pii-detection helm-charts/pii -f helm-charts/pii/values.yaml --namespace model-serving

helm uninstall edu-pii-detection --namespace model-serving
```

## Run Education PII Detection Application

```bash
cd app/frontend

# Get application's usage
python gradio_ui.py -h
python gradio_ui.py --help

# Run application on url 
python gradio_ui.py --url http://pii.<EXTERNAL-IP>.sslip.io/
```