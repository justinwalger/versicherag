terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
  region  = "europe-west1"
}

# The Artifact Registry repo, the github-actions-deployer service account, and
# its IAM grants live in ./bootstrap instead of here - the deployer identity
# used to apply this config isn't (and shouldn't be) allowed to manage IAM on
# itself or the project, so those resources have to be applied separately by
# a privileged identity. See terraform/bootstrap/main.tf.

# fastapi backend
resource "google_cloud_run_v2_service" "fastapi_backend" {
  name     = "fastapi-backend"
  location = "europe-west1"
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = var.backend_image

      env {
        name  = "GEMINI_API_KEY"
        value = var.gemini_api_key
      }
      env {
        name  = "QDRANT_HOST"
        value = var.qdrant_host
      }
      env {
        name  = "QDRANT_API_KEY"
        value = var.qdrant_api_key
      }

      ports {
        container_port = 8080
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  project  = google_cloud_run_v2_service.fastapi_backend.project
  location = google_cloud_run_v2_service.fastapi_backend.location
  name     = google_cloud_run_v2_service.fastapi_backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service" "streamlit_frontend" {
  name     = "streamlit-frontend"
  location = "europe-west1"
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = var.frontend_image

      env {
        name  = "BACKEND_API_URL"
        value = "${google_cloud_run_v2_service.fastapi_backend.uri}/api"
      }

      ports {
        container_port = 8080
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  project  = google_cloud_run_v2_service.streamlit_frontend.project
  location = google_cloud_run_v2_service.streamlit_frontend.location
  name     = google_cloud_run_v2_service.streamlit_frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "frontend_url" {
  description = "public frontend url"
  value       = google_cloud_run_v2_service.streamlit_frontend.uri
}
