#!/bin/bash
set -euo pipefail

export CLOUDSDK_PYTHON="/c/Users/scott/AppData/Local/Google/Cloud SDK/google-cloud-sdk/platform/bundledpython/python.exe"

PROJECT="balmy-limiter-491013-a8"
REGION="us-central1"
SERVICE="lmrf-website"
IMAGE="gcr.io/${PROJECT}/${SERVICE}"

echo "=== LMRF Website Deploy ==="
echo "Project: ${PROJECT}"
echo "Region:  ${REGION}"
echo "Service: ${SERVICE}"
echo ""

# Step 1: Set project
echo "--- Setting project ---"
gcloud config set project "${PROJECT}"

# Step 2: Build container with Cloud Build (builds in the cloud, no local Docker needed)
echo "--- Building container image via Cloud Build ---"
gcloud builds submit --config=cloudbuild.yaml --project="${PROJECT}" .

# Step 3: Deploy to Cloud Run
echo "--- Deploying to Cloud Run ---"
gcloud run deploy "${SERVICE}" \
  --image="${IMAGE}" \
  --platform=managed \
  --region="${REGION}" \
  --port=8080 \
  --allow-unauthenticated \
  --memory=256Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --project="${PROJECT}"

echo "--- Cloud Run service deployed ---"
gcloud run services describe "${SERVICE}" --region="${REGION}" --project="${PROJECT}" --format='value(status.url)'

# Step 4: Reserve a static IP
echo "--- Reserving static external IP ---"
gcloud compute addresses create lmrf-website-ip \
  --global \
  --project="${PROJECT}" 2>/dev/null || echo "Static IP already exists"

STATIC_IP=$(gcloud compute addresses describe lmrf-website-ip --global --project="${PROJECT}" --format='value(address)')
echo "Static IP: ${STATIC_IP}"

# Step 5: Create serverless NEG
echo "--- Creating serverless NEG ---"
gcloud compute network-endpoint-groups create lmrf-website-neg \
  --region="${REGION}" \
  --network-endpoint-type=serverless \
  --cloud-run-service="${SERVICE}" \
  --project="${PROJECT}" 2>/dev/null || echo "NEG already exists"

# Step 6: Create backend service
echo "--- Creating backend service ---"
gcloud compute backend-services create lmrf-website-backend \
  --global \
  --project="${PROJECT}" 2>/dev/null || echo "Backend service already exists"

gcloud compute backend-services add-backend lmrf-website-backend \
  --global \
  --network-endpoint-group=lmrf-website-neg \
  --network-endpoint-group-region="${REGION}" \
  --project="${PROJECT}" 2>/dev/null || echo "Backend already attached"

# Step 7: Create URL map
echo "--- Creating URL map ---"
gcloud compute url-maps create lmrf-website-urlmap \
  --default-service=lmrf-website-backend \
  --global \
  --project="${PROJECT}" 2>/dev/null || echo "URL map already exists"

# Step 8: Create HTTP proxy (start with HTTP; add HTTPS+cert after DNS is pointed)
echo "--- Creating HTTP target proxy ---"
gcloud compute target-http-proxies create lmrf-website-http-proxy \
  --url-map=lmrf-website-urlmap \
  --global \
  --project="${PROJECT}" 2>/dev/null || echo "HTTP proxy already exists"

# Step 9: Create forwarding rule
echo "--- Creating forwarding rule ---"
gcloud compute forwarding-rules create lmrf-website-http-rule \
  --global \
  --target-http-proxy=lmrf-website-http-proxy \
  --address=lmrf-website-ip \
  --ports=80 \
  --project="${PROJECT}" 2>/dev/null || echo "Forwarding rule already exists"

echo ""
echo "=== DEPLOY COMPLETE ==="
echo ""
echo "Cloud Run URL (direct):  $(gcloud run services describe ${SERVICE} --region=${REGION} --project=${PROJECT} --format='value(status.url)')"
echo "Static IP (for DNS):     ${STATIC_IP}"
echo ""
echo "NEXT STEPS:"
echo "  1. Point your domain's DNS A record to ${STATIC_IP}"
echo "  2. Once DNS propagates, add a managed SSL certificate:"
echo "     gcloud compute ssl-certificates create lmrf-website-cert \\"
echo "       --domains=lowermsfoundation.org,www.lowermsfoundation.org \\"
echo "       --global --project=${PROJECT}"
echo "  3. Create HTTPS proxy and forwarding rule:"
echo "     gcloud compute target-https-proxies create lmrf-website-https-proxy \\"
echo "       --url-map=lmrf-website-urlmap --ssl-certificates=lmrf-website-cert \\"
echo "       --global --project=${PROJECT}"
echo "     gcloud compute forwarding-rules create lmrf-website-https-rule \\"
echo "       --global --target-https-proxy=lmrf-website-https-proxy \\"
echo "       --address=lmrf-website-ip --ports=443 --project=${PROJECT}"
