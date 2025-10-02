pipeline {
    agent any

    environment {
        registry = 'qdawwn/edu-pii-detection'
        registry_credentials = 'dockerhub-credentials'
        GCP_PROJECT = 'gifted-object-467904-r0'
        GCP_REGION = 'asia-southeast1'
        CLUSTER = 'gifted-object-467904-r0-gke'
        NAMESPACE = 'model-serving'
        CHART_PATH = './helm-charts/pii'
        RELEASE = 'edu-pii-detection'
        GITHUB_TOKEN = credentials('github_access_token')
        COVERAGE_THRESHOLD = '80'
    }

    stages {
        stage('Test') {
            when {
                anyOf {
                    branch 'main'
                    changeRequest()
                }
            }

            steps {
                sh '''#!bin/bash
                    set -e

                    echo 'Testing with coverage enforcement...'
                    curl -Ls https://astral.sh/uv/install.sh | bash
                    export PATH="$HOME/.local/bin:$PATH"

                    echo "Environment loaded. Testing connection..."

                    uv sync --locked --no-cache

                    echo "Running tests with coverage..."
                    uv run --no-cache pytest --cov=api --cov-report=term-missing --cov-report=xml --cov-config=pyproject.toml --cov-fail-under=${COVERAGE_THRESHOLD}

                    echo "Coverage check passed! Proceeding with pipeline..."
                '''
            }
            post {
                failure {
                    echo "Tests failed or coverage below ${COVERAGE_THRESHOLD}%. Pipeline stopped."
                }
                success {
                    echo "Tests pass with coverage >= ${COVERAGE_THRESHOLD}%. Proceeding to build..."
                }
            }
        }
    }
}