# Ingress Nginx

ingress-nginx is an Ingress controller for Kubernetes using NGINX as a reverse proxy and load balancer.

<div>
  <img src="../../static/picture/NGINX-Ingress-Controller-product-icon.svg" width="300"/>
</div>

# Deploy ingress-nginx with bash script

```bash
#!/bin/bash

# Add ingress-nginx chart to helm repo
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm update

# Pull ingress-nginx chart. We would use version `4.13.2`.
helm pull ingress-nginx/ingress-nginx --version 4.13.2 --untar

# Environments
NAMESPACE="ingress-nginx"

# Create namespace ingress-nginx
echo "Checking namespace: $NAMESPACE"
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "Namespace '$NAMESPACE' not found, creating..."
    kubectl create namespace "$NAMESPACE"
else
    echo "Namespace '$NAMESPACE' already existed, passing."
fi

# Install ingress-nginx
helm upgrade --install ingress-nginx helm-charts/ingress-nginx -f helm-charts/ingress-nginx/values.yaml -n $NAMESPACE
```

## Uninstall ingress-nginx deployment

```bash
helm uninstall ingress-nginx --namespace ingress-nginx
```

# References

[Ingress NGINX Controller](https://github.com/kubernetes/ingress-nginx)

[Ingress](http://kubernetes.io/docs/concepts/services-networking/ingress/)
