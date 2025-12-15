# Internal Actions

This directory contains your organization's custom GitHub Actions that will be included in the catalog. These actions should be golden actions provided by the organization for common workflows and patterns approved by the organization.

## Directory Structure

```
internal/
└── {org-name}/
    └── {action-name}/
        └── action.yml
```

**Example:**
```
internal/
├── platform-team/
│   ├── deploy-to-production/
│   │   └── action.yml
│   └── notify-slack/
│       └── action.yml
└── devops/
    ├── security-scan/
    │   └── action.yml
    └── backup-database/
        └── action.yml
```

## Adding a New Internal Action

### 1. Create the directory structure

```bash
mkdir -p internal/your-org/your-action-name
```

### 2. Create action.yml

```bash
cat > internal/your-org/your-action-name/action.yml << 'EOF'
name: "Deploy to Kubernetes"
description: "Deploy containerized applications to Kubernetes clusters with built-in health checks and rollback support"
author: "Platform Engineering Team"

inputs:
  environment:
    description: "Target environment (dev, staging, prod)"
    required: true
  image-tag:
    description: "Docker image tag to deploy"
    required: true
  namespace:
    description: "Kubernetes namespace"
    required: false
    default: "default"
  replicas:
    description: "Number of pod replicas"
    required: false
    default: "3"
  health-check-timeout:
    description: "Health check timeout in seconds"
    required: false
    default: "300"
  rollback-on-failure:
    description: "Automatically rollback on deployment failure (true/false)"
    required: false
    default: "true"

outputs:
  deployment-url:
    description: "URL of the deployed application"
  deployment-version:
    description: "Deployed version identifier"
  rollback-revision:
    description: "Previous revision number for rollback"

runs:
  using: "composite"
  steps:
    - name: Validate environment
      shell: bash
      run: |
        if [[ ! "${{ inputs.environment }}" =~ ^(dev|staging|prod)$ ]]; then
          echo "❌ Invalid environment: ${{ inputs.environment }}"
          echo "Must be one of: dev, staging, prod"
          exit 1
        fi
        echo "✅ Environment validated: ${{ inputs.environment }}"

    - name: Setup kubectl
      shell: bash
      run: |
        echo "🔧 Setting up kubectl..."
        kubectl version --client

    - name: Configure cluster access
      shell: bash
      run: |
        echo "🔐 Configuring cluster access for ${{ inputs.environment }}..."
        # Your cluster configuration logic here
        # Example: aws eks update-kubeconfig --name my-cluster-${{ inputs.environment }}

    - name: Deploy to Kubernetes
      shell: bash
      run: |
        echo "🚀 Deploying image tag: ${{ inputs.image-tag }}"
        echo "📦 Namespace: ${{ inputs.namespace }}"
        echo "🔢 Replicas: ${{ inputs.replicas }}"

        kubectl set image deployment/myapp \
          myapp=myregistry.io/myapp:${{ inputs.image-tag }} \
          -n ${{ inputs.namespace }}

        kubectl scale deployment/myapp \
          --replicas=${{ inputs.replicas }} \
          -n ${{ inputs.namespace }}

    - name: Wait for rollout
      shell: bash
      run: |
        echo "⏳ Waiting for deployment to complete..."
        kubectl rollout status deployment/myapp \
          -n ${{ inputs.namespace }} \
          --timeout=${{ inputs.health-check-timeout }}s

    - name: Health check
      shell: bash
      run: |
        echo "🏥 Running health checks..."
        PODS=$(kubectl get pods -n ${{ inputs.namespace }} -l app=myapp -o jsonpath='{.items[*].metadata.name}')

        for POD in $PODS; do
          echo "Checking pod: $POD"
          kubectl wait --for=condition=ready pod/$POD \
            -n ${{ inputs.namespace }} \
            --timeout=60s
        done

        echo "✅ All pods are healthy"

    - name: Get deployment info
      shell: bash
      run: |
        echo "📊 Deployment Information:"
        kubectl get deployment myapp -n ${{ inputs.namespace }}

        # Set outputs
        echo "deployment-url=https://myapp-${{ inputs.environment }}.example.com" >> $GITHUB_OUTPUT
        echo "deployment-version=${{ inputs.image-tag }}" >> $GITHUB_OUTPUT

        REVISION=$(kubectl rollout history deployment/myapp -n ${{ inputs.namespace }} | tail -n 2 | head -n 1 | awk '{print $1}')
        echo "rollback-revision=$REVISION" >> $GITHUB_OUTPUT

    - name: Rollback on failure
      if: failure() && inputs.rollback-on-failure == 'true'
      shell: bash
      run: |
        echo "❌ Deployment failed! Rolling back..."
        kubectl rollout undo deployment/myapp -n ${{ inputs.namespace }}
        kubectl rollout status deployment/myapp -n ${{ inputs.namespace }}
        echo "🔄 Rollback completed"
        exit 1
EOF
```

### 3. Rebuild the catalog

```bash
# From project root
./build.sh
```

### 4. Commit and push

```bash
git add blueprints/internal/
git commit -m "Add Kubernetes deployment action"
git push
```

## Best Practices

✅ **Use clear, descriptive names** - Make action names self-explanatory
✅ **Document all inputs/outputs** - Include descriptions for every parameter
✅ **Set required flags** - Mark inputs as required: true/false
✅ **Provide defaults** - Set sensible default values for optional inputs
✅ **Follow naming conventions** - Use kebab-case for action names
✅ **Group by team/org** - Organize actions by owning team
✅ **Add validation** - Validate inputs before executing logic
✅ **Include error handling** - Handle failures gracefully
✅ **Use emojis for clarity** - Make logs easier to read (✅ ❌ 🚀 📦)
✅ **Set outputs** - Provide useful information for downstream steps
