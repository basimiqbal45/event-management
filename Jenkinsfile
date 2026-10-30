pipeline {
    agent any
    triggers { githubPush() }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'ls -la'
            }
        }

        stage('Validate Manifests') {
            steps {
                sh 'kubectl apply --dry-run=client -f k8s/event-app.yaml'
            }
        }

        stage('Build Backend Image') {
            steps {
                sh 'minikube image build -t event-backend:latest backend'
            }
        }

        stage('Build Frontend Image') {
            steps {
                sh 'minikube image build -t event-frontend:latest frontend'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([
                    string(credentialsId: 'event-db-password', variable: 'DB_PASSWORD'),
                    string(credentialsId: 'event-db-root-password', variable: 'DB_ROOT_PASSWORD')
                ]) {
                    sh '''
                        kubectl create secret generic event-db-secret \
                          --from-literal=DB_PASSWORD="$DB_PASSWORD" \
                          --from-literal=DB_ROOT_PASSWORD="$DB_ROOT_PASSWORD" \
                          --dry-run=client -o yaml | kubectl apply -f -
                        kubectl apply -f k8s/event-app.yaml
                        kubectl rollout restart deployment/event-backend deployment/event-frontend
                    '''
                }
            }
        }

        stage('Wait for Rollout') {
            steps {
                sh '''
                    kubectl rollout status deployment/event-db --timeout=300s
                    kubectl rollout status deployment/event-backend --timeout=300s
                    kubectl rollout status deployment/event-frontend --timeout=300s
                '''
            }
        }

        stage('Verify') {
            steps {
                sh '''
                    kubectl get pods,svc
                    URL="http://$(minikube ip):30080/api/health"
                    for i in $(seq 1 15); do
                        if curl -sf --max-time 10 "$URL" | grep -q '"database":"up"'; then
                            echo "Health check passed: app and database are up."; exit 0
                        fi
                        echo "Attempt $i failed, retrying in 10s..."; sleep 10
                    done
                    echo "Health check failed"; exit 1
                '''
            }
        }
    }

    post {
        success { echo 'Event Management deployment completed successfully.' }
        failure { echo 'Deployment failed. Check the console output.' }
    }
}
