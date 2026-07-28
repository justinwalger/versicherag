# Terraform layout

This is split into two separate configs with separate state, on purpose:

- **`main.tf`** (this directory) — the Cloud Run services. Applied automatically by
  the GitHub Actions `deploy.yml` workflow on every push to `main`, authenticated as
  the `github-actions-deployer` service account.
- **`bootstrap/`** — the Artifact Registry repo, the `github-actions-deployer` service
  account itself, and its IAM grants. Applied manually, rarely, by a human with
  privileged GCP access. Never run by CI.

## Why not just one config?

`github-actions-deployer` is deliberately scoped narrowly (Cloud Run deploy rights
only) so a leaked `GCP_CREDENTIALS` secret can't grant itself broader project access.
That means it can't manage its own IAM grants or the registry's admin settings - if
those resources lived in this directory, every CI-driven `terraform apply` would try
to reconcile them and fail with a permissions error, every time.

## When to touch `bootstrap/`

Only when changing the deployer's permissions, the registry's cleanup policy, or
anything else identity-related. Apply it manually with your own privileged
credentials (`gcloud auth application-default login`), from `terraform/bootstrap`,
with its own state prefix (`flexopus-bootstrap`, vs. `flexopus` for the root config,
same GCS bucket).

Day-to-day deploys never need this directory.
