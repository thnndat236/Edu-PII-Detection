#!/bin/bash

set -e

# Default values
NAMESPACE="ingress-nginx"
CHART_VERSION="4.13.2"
CHART_BASE_DIR="helm-charts"
CHART_DIR="$CHART_BASE_DIR/ingress-nginx"

# Function to display usage
usage() {
    echo "Usage: $0 {add-pull|install|check-ip|uninstall}"
    echo "  add-pull    : Add Helm repo and pull ingress-nginx chart"
    echo "  install     : Create namespace and install ingress-nginx"
    echo "  check-ip    : Check the external IP of ingress-nginx-controller service"
    echo "  uninstall   : Uninstall ingress-nginx"
    exit 1
}

# Check if an argument is provided
if [ $# -ne 1 ]; then
    usage
fi

# Add Helm repo and pull chart
add_and_pull() {
    echo "Adding ingress-nginx chart to Helm repo..."
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx || { echo "Failed to add repo"; exit 1; }
    helm repo update || { echo "Failed to update repo"; exit 1; }

    # Ensure CHART_BASE_DIR exists
    mkdir -p "$CHART_BASE_DIR" || { echo "Failed to create directory $CHART_BASE_DIR"; exit 1; }

    echo "Pulling ingress-nginx chart (version $CHART_VERSION)..."
    helm pull ingress-nginx/ingress-nginx --version "$CHART_VERSION" --untar --destination "$CHART_BASE_DIR" || { echo "Failed to pull chart"; exit 1; }
    echo "Chart pulled and untarred to $CHART_BASE_DIR successfully."
}

# Create namespace and install ingress-nginx
install() {
    echo "Checking namespace: $NAMESPACE"
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        echo "Namespace '$NAMESPACE' not found, creating..."
        kubectl create namespace "$NAMESPACE" || { echo "Failed to create namespace"; exit 1; }
    else
        echo "Namespace '$NAMESPACE' already existed, passing."
    fi
    echo "Installing ingress-nginx..."
    helm upgrade --install ingress-nginx "$CHART_DIR" -f "$CHART_DIR/values.yaml" -n "$NAMESPACE" || { echo "Failed to install ingress-nginx"; exit 1; }
    echo "Ingress-nginx installed successfully."
}

# Check external IP of ingress-nginx-controller service
check_ip() {
    echo "Checking external IP of ingress-nginx-controller service..."
    kubectl get service --namespace "$NAMESPACE" ingress-nginx-controller --output wide || { echo "Failed to get service details"; exit 1; }
}

# Uninstall ingress-nginx
uninstall() {
    echo "Uninstalling ingress-nginx..."
    helm uninstall ingress-nginx -n "$NAMESPACE" || { echo "Failed to uninstall ingress-nginx"; exit 1; }
    echo "Ingress-nginx uninstalled successfully."
    
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
        "check-ip")
            check_ip
            ;;
        "uninstall")
            uninstall
            ;;
        *)
            usage
            ;;
    esac
}

main "$@"