#!/bin/bash

set -e

# environments
NAMESPACE="monitoring"
CHART_VERSION="77.5.0"
CHART_BASE_DIR="helm-charts"
CHART_DIR="$CHART_BASE_DIR/kube-prometheus-stack"

# Function to display usage
usage() {
    echo "Usage: $0 {add-pull|install|get-credentials|uninstall}"
    echo "  add-pull        : Add Helm repo and pull kube-prometheus-stack charts"
    echo "  install         : Create namespace and install kube-prometheus-stack"
    echo "  get-credentials : Get Grafana credentials for login"
    echo "  uninstall       : Uninstall kube-prometheus-stack"
    exit 1
}

# Add prometheus-community/kube-prometheus-stack Helm charts repo and pull chart
add_and_pull() {
    echo "Adding prometheus-community to Helm repo..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || { echo "Failed to add repo"; exit 1; }
    helm repo update || { echo "Failed to update repo"; exit 1; }
    
    # Ensure CHART_BASE_DIR exists
    mkdir -p "$CHART_BASE_DIR" || { echo "Failed to create directory $CHART_BASE_DIR"; exit 1; }

    # kube-prometheus-stack
    echo "Pulling kube-prometheus-stack chart (version $CHART_VERSION)..."
    helm pull prometheus-community/kube-prometheus-stack --version "$CHART_VERSION" --untar --destination "$CHART_BASE_DIR" || { echo "Failed to pull kube-prometheus-stack chart"; exit 1; }
    echo "Chart pulled and untarred to $CHART_BASE_DIR successfully."
}

# Create namespace and install kube-prometheus-stack
install() {
    # Create namespace monitoring
    echo "Checking namespace: $NAMESPACE"
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        echo "Namespace '$NAMESPACE' not found, creating..."
        kubectl create namespace "$NAMESPACE"
    else
        echo "Namespace '$NAMESPACE' already exists, passing."
    fi

    # Install kube-prometheus-stack
    echo "Installing kube-prometheus-stack..."
    helm upgrade --install kube-prometheus-stack "$CHART_DIR" -f "$CHART_DIR/values.yaml" -n "$NAMESPACE" || { echo "Failed to install kube-prometheus-stack"; exit 1; }

    echo "kube-prometheus-stack installed successfully. Verifying rollout..."

    # Verify Prometheus rollout
    kubectl rollout status statefulset/prometheus-kube-prometheus-stack-prometheus -n "$NAMESPACE" --timeout=300s || { echo "Prometheus rollout failed"; exit 1; }

    # Verify Alertmanager rollout
    kubectl rollout status statefulset/alertmanager-kube-prometheus-stack-alertmanager -n "$NAMESPACE" --timeout=300s || { echo "Alertmanager rollout failed"; exit 1; }

    # Verify Grafana rollout
    kubectl rollout status deployment/kube-prometheus-stack-grafana -n "$NAMESPACE" --timeout=300s || { echo "Grafana rollout failed"; exit 1; }

    echo "All kube-prometheus-stack components rolled out successfully."
}

# Function to get access credentials
get_credentials() {
    echo "Fetching kube-prometheus-stack-grafana credentials from namespace: $NAMESPACE"
    
    # Get Grafana admin password
    if kubectl get secret kube-prometheus-stack-grafana -n "$NAMESPACE" &> /dev/null; then
        local grafana_password=$(kubectl get secret kube-prometheus-stack-grafana -n "$NAMESPACE" -o jsonpath='{.data.admin-password}' | base64 --decode)
        
        echo "Grafana credentials retrieved!"
        echo "Username: admin"
        echo "Password: $grafana_password"
    else
        echo "Secret 'kube-prometheus-stack-grafana' not found in namespace '$NAMESPACE'."
    fi
}

# Uninstall kube-prometheus-stack
uninstall() {
    echo "Uninstalling kube-prometheus-stack..."
    helm uninstall kube-prometheus-stack -n "$NAMESPACE" || { echo "Failed to uninstall kube-prometheus-stack"; exit 1; }
    echo "kube-prometheus-stack uninstalled successfully."

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
        "get-credentials")
            get_credentials
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