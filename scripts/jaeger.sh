#!/bin/bash

# Environments
NAMESPACE="tracing"
CHART_VERSION="3.4.1" 
CHART_BASE_DIR="helm-charts"
CHART_DIR="$CHART_BASE_DIR/jaeger"

# Function to display usage
usage() {
    echo "Usage: $0 {add-pull|install|copy-credentials|verify|uninstall}"
    echo "  add-pull         : Add Helm repo and pull Jaeger chart"
    echo "  install          : Create namespace and install Jaeger"
    echo "  copy-credentials : Copy credentials from logging to tracing namespace"
    echo "  verify           : Verify Elasticsearch connectivity"
    echo "  uninstall        : Uninstall Jaeger"
    exit 1
}

# Add Jaeger Helm chart repo and pull chart
add_and_pull() {
    echo "Adding Jaeger chart to Helm repo..."
    helm repo add jaegertracing https://jaegertracing.github.io/helm-charts || { echo "Failed to add repo"; exit 1; }
    helm repo update || { echo "Failed to update repo"; exit 1; }
    
    # Ensure CHART_BASE_DIR exists
    mkdir -p "$CHART_BASE_DIR" || { echo "Failed to create directory $CHART_BASE_DIR"; exit 1; }

    echo "Pulling Jaeger chart (version $CHART_VERSION)..."
    helm pull jaegertracing/jaeger --version "$CHART_VERSION" --untar --destination "$CHART_BASE_DIR" || { echo "Failed to pull Jaeger chart"; exit 1; }
    echo "Chart pulled and untarred to $CHART_BASE_DIR successfully."
}

# Create namespace and copy Elasticsearch credentials from logging to tracing namespace
copy_credentials() {
    echo "Checking namespace: $NAMESPACE"
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        echo "Namespace '$NAMESPACE' not found, creating..."
        kubectl create namespace "$NAMESPACE" || { echo "Failed to create namespace"; exit 1; }
    else
        echo "Namespace '$NAMESPACE' already existed, passing."
    fi
    
    echo "Copying elasticsearch credentials from logging to tracing namespace..."

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

    echo "Copy to tracing namespace successfully."
}


# Create namespace and install Jaeger
install() {
    echo "Checking namespace: $NAMESPACE"
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        echo "Namespace '$NAMESPACE' not found, creating..."
        kubectl create namespace "$NAMESPACE" || { echo "Failed to create namespace"; exit 1; }
    else
        echo "Namespace '$NAMESPACE' already existed, passing."
    fi

    echo "Installing Jaeger..."
    helm upgrade --install jaeger "$CHART_DIR" -f "$CHART_DIR/values.yaml" --namespace "$NAMESPACE" || { echo "Failed to install Jaeger"; exit 1; }

    echo "Jaeger installed successfully. Verifying..."
    kubectl rollout status deployment/jaeger -n "$NAMESPACE" --timeout=300s || { echo "Jaeger rollout failed"; exit 1; }
    echo "All Jaeger components rolled out successfully."
}

# Verify Elasticsearch connectivity
verify_deployment() {
    echo "Verifying Elasticsearch connectivity (DNS resolution)..."
    kubectl exec deployment/jaeger  -n "$NAMESPACE" -- \
      nslookup elasticsearch.logging.svc.cluster.local || { echo "Jaeger verify failed"; exit 1; }
    echo "All Jaeger components rolled out successfully."

    echo "Checking Jaeger logs for Elasticsearch connection..."
    kubectl logs deployment/jaeger -n "$NAMESPACE" --tail=100 | grep -i elasticsearch
}


# Uninstall Jaeger
uninstall() {
    echo "Uninstalling Jaeger..."
    helm uninstall jaeger --namespace "$NAMESPACE" || { echo "Failed to uninstall Jaeger"; exit 1; }
    echo "Jaeger uninstalled successfully."

    echo "Checking namespace: $NAMESPACE"
    if kubectl get namespace "$NAMESPACE" &>/dev/null; then
        echo "Namespace '$NAMESPACE' still exists. You may want to delete it manually with: kubectl delete namespace $NAMESPACE"
    fi
}

# Main script logic
main() {
    case "$1" in
        "add-pull")
            add_and_pull
            ;;
        "install")
            install
            ;;
        "copy-credentials")
            copy_credentials
            ;;
        "uninstall")
            uninstall
            ;;
        "verify")
            verify_deployment
            ;;
        *)
            usage
            ;;
    esac
}

# Ensure the script runs with proper permissions
if [ ! -x "$0" ]; then
    echo "Granting execute permission to the script..."
    chmod +x "$0"
fi

main "$@"