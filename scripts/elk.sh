#!/bin/bash

set -e

# environments
NAMESPACE="logging"
CHART_VERSION="8.5.1"
CHART_DIR="helm-charts/elk-stack"

# Function to display usage
usage() {
    echo "Usage: $0 {add-pull|install|get-credentials|uninstall}"
    echo "  add-pull        : Add Helm repo and pull ELK stack charts"
    echo "  install         : Create namespace and install ELK stack"
    echo "  get-credentials : Get Elasticsearch credentials for Kibana login"
    echo "  uninstall       : Uninstall ELK stack"
    exit 1
}

# Add Elastic Helm charts repo and pull chart
add_and_pull() {
    echo "Adding elastic chart to Helm repo..."
    helm repo add elastic https://helm.elastic.co || { echo "Failed to add repo"; exit 1; }
    helm repo update || { echo "Failed to update repo"; exit 1; }
    
    # Ensure CHART_DIR exists
    mkdir -p "$CHART_DIR" || { echo "Failed to create directory $CHART_DIR"; exit 1; }

    # Elasticsearch
    echo "Pulling elasticsearch chart (version $CHART_VERSION)..."
    helm pull elastic/elasticsearch --version "$CHART_VERSION" --untar --destination "$CHART_DIR" || { echo "Failed to pull elasticsearch chart"; exit 1; }
    echo "Chart pulled and untarred to ${CHART_DIR}/elasticsearch successfully."

    # Filebeat
    echo "Pulling filebeat chart (version $CHART_VERSION)..."
    helm pull elastic/filebeat --version "$CHART_VERSION" --untar --destination "$CHART_DIR" || { echo "Failed to pull filebeat chart"; exit 1; }
    echo "Chart pulled and untarred to ${CHART_DIR}/filebeat successfully."

    # Logstash
    echo "Pulling logstash chart (version $CHART_VERSION)..."
    helm pull elastic/logstash --version "$CHART_VERSION" --untar --destination "$CHART_DIR" || { echo "Failed to pull logstash chart"; exit 1; }
    echo "Chart pulled and untarred to ${CHART_DIR}/logstash successfully."

    # Kibana
    echo "Pulling kibana chart (version $CHART_VERSION)..."
    helm pull elastic/kibana --version "$CHART_VERSION" --untar --destination "$CHART_DIR" || { echo "Failed to pull kibana chart"; exit 1; }
    echo "Chart pulled and untarred to ${CHART_DIR}/kibana successfully."
}

# Create namespace and install ELK
install() {
    # Create namespace logging
    echo "Checking namespace: $NAMESPACE"
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        echo "Namespace '$NAMESPACE' not found, creating..."
        kubectl create namespace "$NAMESPACE"
    else
        echo "Namespace '$NAMESPACE' already existed, passing."
    fi

    # Install Elasticsearch
    echo "Installing Elasticsearch..."
    helm upgrade --install elasticsearch "${CHART_DIR}/elasticsearch" -f "${CHART_DIR}/elasticsearch/values.yaml" -n "$NAMESPACE" || { echo "Failed to install Elasticsearch"; exit 1; }

    # Install Filebeat
    echo "Installing Filebeat..."
    helm upgrade --install filebeat "${CHART_DIR}/filebeat" -f "${CHART_DIR}/filebeat/values.yaml" -n "$NAMESPACE" || { echo "Failed to install Filebeat"; exit 1; }

    # Install Logstash
    echo "Installing Logstash..."
    helm upgrade --install logstash "${CHART_DIR}/logstash" -f "${CHART_DIR}/logstash/values.yaml" -n "$NAMESPACE" || { echo "Failed to install Logstash"; exit 1; }

    # Install Kibana
    echo "Installing Kibana..."
    helm upgrade --install kibana "${CHART_DIR}/kibana" -f "${CHART_DIR}/kibana/values.yaml" -n "$NAMESPACE" || { echo "Failed to install Kibana"; exit 1; }

    echo "ELK Stack installed successfully. Verifying..."
    kubectl rollout status statefulset/elasticsearch -n "$NAMESPACE" --timeout=300s || { echo "Elasticsearch rollout failed"; exit 1; }
    kubectl rollout status deployment/filebeat -n "$NAMESPACE" --timeout=300s || { echo "Filebeat rollout failed"; exit 1; }
    kubectl rollout status deployment/logstash -n "$NAMESPACE" --timeout=300s || { echo "Logstash rollout failed"; exit 1; }
    kubectl rollout status deployment/kibana -n "$NAMESPACE" --timeout=300s || { echo "Kibana rollout failed"; exit 1; }
    echo "All components rolled out successfully."
}

# Get Elasticsearch credentials for Kibana login
get_credentials() {
    echo "Fetching Elasticsearch credentials from namespace: $NAMESPACE"

    # Get Elasticsearch password
    if kubectl get secret elasticsearch-credentials -n "$NAMESPACE" &>/dev/null; then
        local elasticsearch_username=$(kubectl get secret elasticsearch-credentials -n "$NAMESPACE" -o jsonpath='{.data.username}' | base64 --decode)
        local elasticsearch_password=$(kubectl get secret elasticsearch-credentials -n "$NAMESPACE" -o jsonpath='{.data.password}' | base64 --decode)
        
        echo "Elasticsearch credentials retrieved!"
        echo "Username: $elasticsearch_username"
        echo "Password: $elasticsearch_password"
    else
        echo "Secret 'elasticsearch-credentials' not found in namespace '$NAMESPACE'."
    fi
}


# Uninstall ELK Stack
uninstall() {
    echo "Uninstalling Kibana..."
    helm uninstall kibana -n "$NAMESPACE" || { echo "Failed to uninstall Kibana"; exit 1; }
    echo "Kibana uninstalled successfully."

    echo "Uninstalling Filebeat..."
    helm uninstall filebeat -n "$NAMESPACE" || { echo "Failed to uninstall Filebeat"; exit 1; }
    echo "filebeat uninstalled successfully."

    echo "Uninstalling Logstash..."
    helm uninstall logstash -n "$NAMESPACE" || { echo "Failed to uninstall Logstash"; exit 1; }
    echo "logstash uninstalled successfully."

    echo "Uninstalling Elasticsearch..."
    helm uninstall elasticsearch -n "$NAMESPACE" || { echo "Failed to uninstall Elasticsearch"; exit 1; }
    echo "Elasticsearch uninstalled successfully."


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