# Lower Mississippi River Foundation (LMRF)

## About
LMRF is a separate nonprofit organization. Scott Shirey is on the board and provides technical support. This is NOT a Confluence Point Consulting project.

## Structure
- `website/` — LMRF website deploy files (lowermsfoundation.org)
- `scrape/` — Migration tools used to move LMRF site from Squarespace to GCP

## GCP
- **Project:** `balmy-limiter-491013-a8`
- **Account:** `info@lowermsfoundation.org`
- **Region:** `us-central1`
- **Static IP:** `34.36.117.211`
- **Cloud Run service:** `lmrf-website`
- **SSL:** `lmrf-website-cert` (Google-managed, ACTIVE for lowermsfoundation.org + www)
- **Domain:** `lowermsfoundation.org`

## Rules
- This is NOT a CPC project. Do not touch `confluence-point-consulting` project or any `cpc-*` resources.
- Authenticate as `info@lowermsfoundation.org` when working in this project.
- Python path for gcloud: `export CLOUDSDK_PYTHON="/c/Users/scott/AppData/Local/Google/Cloud SDK/google-cloud-sdk/platform/bundledpython/python.exe"`

## Deploy
```bash
export CLOUDSDK_PYTHON="/c/Users/scott/AppData/Local/Google/Cloud SDK/google-cloud-sdk/platform/bundledpython/python.exe"
gcloud config set account info@lowermsfoundation.org
gcloud config set project balmy-limiter-491013-a8
cd ~/lmrf/website && bash deploy.sh
```
