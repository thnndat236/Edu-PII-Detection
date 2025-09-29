# Edu-PII-Detection

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
python gradio_ui.py --url pii.<EXTERNAL-IP>.sslip.io/
```