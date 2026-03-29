# Deploy LMRF Static Site to GCP Cloud Storage

## Prerequisites
- Google Cloud SDK (`gcloud`) installed and authenticated
- A GCP project with billing enabled
- A domain name (optional, for custom domain)

## Step 1: Create a Cloud Storage Bucket

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Create bucket (use your domain name as bucket name for custom domain)
gsutil mb -l us-central1 gs://www.lowermsfoundation.org

# Or use a generic bucket name
# gsutil mb -l us-central1 gs://lmrf-website
```

## Step 2: Configure the Bucket for Static Website Hosting

```bash
# Set the main page and 404 page
gsutil web set -m index.html -e index.html gs://www.lowermsfoundation.org

# Make the bucket publicly readable
gsutil iam ch allUsers:objectViewer gs://www.lowermsfoundation.org
```

## Step 3: Upload the Site

```bash
# From the site/ directory, upload everything
cd /path/to/lmrf-scrape/site
gsutil -m rsync -r -d . gs://www.lowermsfoundation.org

# Set correct content types for common files
gsutil -m setmeta -h "Content-Type:text/html" gs://www.lowermsfoundation.org/*.html
gsutil -m setmeta -h "Content-Type:text/html" gs://www.lowermsfoundation.org/blog/*.html
gsutil -m setmeta -h "Content-Type:text/css" gs://www.lowermsfoundation.org/css/*.css
gsutil -m setmeta -h "Content-Type:application/javascript" gs://www.lowermsfoundation.org/js/*.js

# Set cache headers for images (cache for 1 week)
gsutil -m setmeta -h "Cache-Control:public, max-age=604800" gs://www.lowermsfoundation.org/images/*
```

## Step 4: Test the Site

Visit: `https://storage.googleapis.com/www.lowermsfoundation.org/index.html`

## Step 5: Set Up Custom Domain (Optional)

### Option A: Using Cloud Storage directly (HTTP only)
1. Verify domain ownership in Google Search Console
2. Create a CNAME record pointing `www.lowermsfoundation.org` to `c.storage.googleapis.com`

### Option B: Using Cloud CDN + Load Balancer (HTTPS - Recommended)

```bash
# 1. Reserve a static IP
gcloud compute addresses create lmrf-ip --global

# 2. Create a backend bucket
gcloud compute backend-buckets create lmrf-backend \
  --gcs-bucket-name=www.lowermsfoundation.org \
  --enable-cdn

# 3. Create a URL map
gcloud compute url-maps create lmrf-url-map \
  --default-backend-bucket=lmrf-backend

# 4. Create an SSL certificate (managed)
gcloud compute ssl-certificates create lmrf-cert \
  --domains=www.lowermsfoundation.org \
  --global

# 5. Create an HTTPS proxy
gcloud compute target-https-proxies create lmrf-https-proxy \
  --url-map=lmrf-url-map \
  --ssl-certificates=lmrf-cert

# 6. Create a forwarding rule
gcloud compute forwarding-rules create lmrf-https-rule \
  --global \
  --target-https-proxy=lmrf-https-proxy \
  --address=lmrf-ip \
  --ports=443

# 7. Get the IP address
gcloud compute addresses describe lmrf-ip --global --format="value(address)"

# 8. Update DNS: Point www.lowermsfoundation.org A record to that IP
```

## Updating the Site

```bash
# After making changes, re-sync:
cd /path/to/lmrf-scrape/site
gsutil -m rsync -r -d . gs://www.lowermsfoundation.org
```

## Cost Estimate
- Storage: ~$0.02/month (60MB of files)
- Network: ~$0.10-0.50/month for light traffic
- Load Balancer (if using HTTPS): ~$18/month
- SSL Certificate: Free (Google-managed)
