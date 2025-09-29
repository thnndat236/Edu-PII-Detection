# Jaeger

Jaeger is an open-source, end-to-end distributed tracing system. It is used for monitoring and troubleshooting the performance of microservices-based applications. With Jaeger, developers can track requests as they flow through different services, visualize dependencies, measure latencies, and identify performance bottlenecks or errors.

Jaeger is a distributed tracing platform released as open source by Uber Technologies  in 2016 and donated to Cloud Native Computing Foundation  where it is a graduated project.

<div>
  <img src="../../static/picture/Jaeger_Logo_Final_PANTONE REVERSE.svg" width="300"/>
</div>

# OpenTelemetry

OpenTelemetry is a set of APIs and SDKs that allows developers to collect and export traces, logs, and metrics. It enables instrumentation of cloud-native applications, allowing developers to collect telemetry data that helps them understand their software’s performance and behavior. 

OpenTelemetry is the way of the future – it’s open-source and vendor-neutral, meaning that developers avoid vendor lock-in. It enables effective observability so devs can easily pinpoint key issues and resolve them faster. 

<div>
  <img src="../../static/picture/opentelemetry-horizontal-color.svg" width="300"/>
</div>

# Manual step-by-step Setting Jaeger

**Kubernetes Cluster**: Create namespace `tracing`:

```bash
kubectl create ns tracing
```

**Helm Repository**: Add this chart to Helm repo, it contains all repo for Jaeger stack

```bash
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo update
```

---

**Step 1**: Pull jaeger chart. We would use version `3.4.1`.

```bash
helm pull jaegertracing/jaeger --version 3.4.1 --untar
```

**Step 2**: Editing Jaeger configuration file `jaeger/values.yaml`

2.1. Enable Jaeger all-in-one and disable jaeger-collector, jaeger-query, jaeger-agent:

```yaml
allInOne:
  enabled: true
  replicas: 1
  image:
    registry: ""
    repository: jaegertracing/all-in-one
    tag: ""
    digest: ""
    pullPolicy: IfNotPresent
    pullSecrets: []
  extraEnv: []
  extraSecretMounts:
    - name: elasticsearch-certs
      mountPath: /usr/share/jaeger/config/elasticsearch-certs
      secretName: elasticsearch-certs
      readOnly: true
  ...
  service:
    headless: false
    collector:
      otlp:
        grpc:
          name: otlp-grpc
          port: 4317
        http:
          name: otlp-http
          port: 4318
  ingress:
    enabled: true
    ingressClassName: nginx
    annotations:
      nginx.ingress.kubernetes.io/rewrite-target: /
    labels: {}
    hosts:
      - jaeger.<EXTERNAL_IP>.sslip.io
    tls: []
    pathType: Prefix
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 256m
      memory: 128Mi
  ...
```

```yaml
query:
  enabled: false

collector:
  enabled: false

agent:
  enabled: false
```

2.2. Use existing elasticsearch

```yaml
provisionDataStore:
  cassandra: false
  elasticsearch: false
  kafka: false
```

2.3. Use Elasticsearch for persistant trace storage:

```yaml
storage:
  # allowed values (cassandra, elasticsearch, grpc-plugin, badger, memory)
  type: elasticsearch
  elasticsearch:
    scheme: https
    host: elasticsearch.logging.svc
    port: 9200
    anonymous: false
    user: elastic
    usePassword: true
    # password: changeme
    indexPrefix: jaeger
    ## Use existing secret (ignores previous password)
    existingSecret: elasticsearch-credentials
    existingSecretKey: password
    nodesWanOnly: false
    extraEnv: []
    ## ES related cmd line opts to be configured on the concerned components
    cmdlineParams:
      es.server-urls: https://elasticsearch.logging.svc:9200
      es.username: elastic
      es.index-prefix: jaeger
      es.tls.ca: /usr/share/jaeger/config/elasticsearch-certs/ca.crt
    tls:
      enabled: true
      secretName: elasticsearch-certs
      # The mount properties of the secret
      mountPath: /usr/share/jaeger/config/elasticsearch-certs/ca.crt
      subPath: ca.crt
      # How ES_TLS_CA variable will be set in the various components
      ca: /usr/share/jaeger/config/elasticsearch-certs/ca.crt
```

**Step 3**: Copy Elasticsearch Credentials

```bash
# Copy credentials from logging to tracing namespace
kubectl get secret elasticsearch-credentials -n logging -o yaml | \
  sed 's/namespace: logging/namespace: tracing/' | \
  sed '/resourceVersion:/d' | \
  sed '/uid:/d' | \
  sed '/creationTimestamp:/d' | \
  kubectl apply -f -

# Copy certificates for TLS connection
kubectl get secret elasticsearch-certs -n logging -o yaml | \
  sed 's/namespace: logging/namespace: tracing/' | \
  sed '/resourceVersion:/d' | \
  sed '/uid:/d' | \
  sed '/creationTimestamp:/d' | \
  kubectl apply -f -
```

**Step 4**: Deploying Jaeger using Helm's `helm upgrade` command

```bash
helm upgrade --install jaeger helm-charts/jaeger -f helm-charts/jaeger/values.yaml --namespace tracing
```

**Step 5**: Deploy Jaeger 

Execute elasticsearch.sh file using bash to deploy Jaeger:

```bash
bash scripts/jaeger.sh
```

**Step 6**: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n tracing

# Check services
kubectl get svc -n tracing

# Check ingress
kubectl get ingress -n tracing

# Verify Elasticsearch connectivity (DNS resolution)
kubectl exec deployment/jaeger -n tracing  -- \
  nslookup elasticsearch.logging.svc.cluster.local

# kubectl exec -n tracing deployment/jaeger-collector -- \
#   nslookup elasticsearch
# kubectl exec -n tracing deployment/jaeger-query -- \
#   nslookup elasticsearch

# Check Jaeger logs for Elasticsearch connection
kubectl logs deployment/jaeger -n tracing --tail=100 | grep -i elasticsearch

# kubectl logs -n tracing deployment/jaeger-collector --tail=100 | grep -i elasticsearch
# kubectl logs -n tracing deployment/jaeger-query --tail=100 | grep -i elasticsearch
```

Step 7: Accessing Jaeger UI

```bash
# Get Jaeger UI URL automatically
JAEGER_HOST=$(kubectl get ingress -n tracing -o jsonpath='{.items[0].spec.rules[0].host}')
echo "Jaeger UI: http://$JAEGER_HOST"

# Port forward for local access (if ingress not available)
kubectl port-forward -n tracing svc/jaeger-query 16686:16686
# Then access: http://localhost:16686
```
---
# Deploy with bash script

```bash
#!/bin/bash

# Environments
NAMESPACE="tracing"

# Create namespace logging
echo "Checking namespace: $NAMESPACE"
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "Namespace '$NAMESPACE' not found, creating..."
    kubectl create namespace "$NAMESPACE"
else
    echo "Namespace '$NAMESPACE' already existed, passing."
fi


# Install Jaeger
helm upgrade --install jaeger helm-charts/jaeger -f helm-charts/jaeger/values.yaml --namespace $NAMESPACE
```

## Uninstall Jaeger deployment

```bash
helm uninstall jaeger --namespace tracing
```

---
# References

[Jaeger](https://www.jaegertracing.io/)

[Jaeger Tracing: A Friendly Guide for Beginners](https://medium.com/jaegertracing/jaeger-tracing-a-friendly-guide-for-beginners-7b53a4a568ca)

[Introducing native support for OpenTelemetry in Jaeger](https://medium.com/jaegertracing/introducing-native-support-for-opentelemetry-in-jaeger-eb661be8183c)

[Adaptive Sampling in Jaeger](https://medium.com/jaegertracing/adaptive-sampling-in-jaeger-50f336f4334)