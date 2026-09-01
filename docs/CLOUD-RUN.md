# Cloud Run deployment

CutoverProof serves the React portal, FastAPI API, and an ephemeral PostgreSQL 17 sandbox from one Cloud Run container. The sandbox exists only to execute synthetic assessment packs; production targets are refused in code.

## Current demo deployment

- Service: `cutoverproof`
- Region: `us-central1`
- Project: `project-ca8af2fe-5aff-496a-bd8`
- Public URL: `https://cutoverproof-1021060138341.us-central1.run.app`
- Cloud Build: `fa3aee25-644d-44f8-ada0-adca5a3e6b34` (`SUCCESS`)
- Image: `us-central1-docker.pkg.dev/project-ca8af2fe-5aff-496a-bd8/hackathon-apps/cutoverproof:fa3aee25-644d-44f8-ada0-adca5a3e6b34`
- Image digest: `sha256:151a50328c402532cf54e924003b916ef953d698f6f9d929ea41bfb0a07984a6`
- Revision: `cutoverproof-00007-mrc` (100% traffic)
- Runtime identity: `cutoverproof-runner@project-ca8af2fe-5aff-496a-bd8.iam.gserviceaccount.com`
- Runtime: two vCPU, 2 GiB, concurrency 1, zero to two instances, 900-second request timeout
- Model: `gemini-3.1-flash-lite` through Vertex AI

The runtime identity has the narrow `roles/aiplatform.user` permission and secret-level access to the reviewer password in Secret Manager. On 2026-09-01 the public service passed health, authenticated sign-in, live Vertex planning, PostgreSQL counterexample execution, named approval, and identical-schedule repair replay. See [`LIVE-DEPLOYMENT-VERIFICATION.md`](LIVE-DEPLOYMENT-VERIFICATION.md).

## Why PostgreSQL is inside this container

The harness deliberately drops and recreates `public` before every candidate. For a bounded demonstration, an ephemeral database inside the same instance gives three useful guarantees:

1. the database cannot be confused with a production target;
2. every new instance starts clean; and
3. the entire judge path remains one reproducible image.

The entrypoint creates only the exact allow-listed target:

- host: `127.0.0.1`
- database: `cutoverproof_sandbox`
- user: `cutover`

This is not a multi-tenant production topology. A production version would use a queue, durable job state, object storage, and a separate disposable database per assessment.

## Build

```powershell
$project = "YOUR_PROJECT"
$region = "us-central1"
$repository = "YOUR_ARTIFACT_REPOSITORY"
$image = "$region-docker.pkg.dev/$project/$repository/cutoverproof:demo"

docker build -t $image .
docker push $image
```

## Least-privilege Vertex identity

Create a dedicated service account and grant only the prediction role:

```powershell
gcloud iam service-accounts create cutoverproof-runner `
  --project $project `
  --display-name "CutoverProof Cloud Run runner"

gcloud projects add-iam-policy-binding $project `
  --member "serviceAccount:cutoverproof-runner@$project.iam.gserviceaccount.com" `
  --role "roles/aiplatform.user"
```

No Gemini API key is required when Vertex AI application-default credentials are used.

## Deploy

```powershell
gcloud run deploy cutoverproof `
  --project $project `
  --image $image `
  --region $region `
  --service-account "cutoverproof-runner@$project.iam.gserviceaccount.com" `
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=$project,GOOGLE_CLOUD_LOCATION=global,MODEL_NAME=gemini-3.1-flash-lite,CUTOVERPROOF_DEMO_EMAIL=judge@cutoverproof.dev,CUTOVERPROOF_COOKIE_SECURE=true" `
  --set-secrets "CUTOVERPROOF_DEMO_PASSWORD=cutoverproof-demo-password:latest" `
  --memory 2Gi `
  --cpu 2 `
  --concurrency 1 `
  --max-instances 2 `
  --min-instances 0 `
  --timeout 900 `
  --allow-unauthenticated
```

The interface polls an active job while it runs. In-memory job state is appropriate for this single-user demonstration; a production service would move jobs to durable queue-backed workers.

## Verify

```powershell
$url = gcloud run services describe cutoverproof `
  --project $project `
  --region $region `
  --format "value(status.url)"

Invoke-RestMethod "$url/api/health"
```

Then sign in, load the built-in example, run it with a candidate budget of four, inspect the violating row, approve the allow-listed repair, and confirm the identical-schedule replay passes.

## Automated release

The checked-in `cloudbuild.yaml` defines backend tests against disposable PostgreSQL, frontend tests and type-checking, a versioned container build, and an Artifact Registry push. Deployment is intentionally a separate operator step so the build identity does not need persistent Cloud Run administrator access.

```powershell
gcloud builds submit --project $project --config cloudbuild.yaml .
```

Deploy the immutable digest printed by the successful build:

```powershell
gcloud run deploy cutoverproof `
  --project $project `
  --region $region `
  --image "$region-docker.pkg.dev/$project/$repository/cutoverproof@sha256:IMAGE_DIGEST" `
  --quiet
```

## Rollback

List the service revisions, then direct all traffic to the previous healthy revision:

```powershell
gcloud run revisions list --project $project --region $region --service cutoverproof
gcloud run services update-traffic cutoverproof --project $project --region $region --to-revisions "PREVIOUS_REVISION=100"
Invoke-RestMethod "$url/api/health"
```
