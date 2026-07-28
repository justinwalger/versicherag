variable "project_id" {
  description = "gcp project id"
  type        = string
}

variable "backend_image" {
  description = "Fully qualified image tag for the FastAPI backend (e.g. from Artifact Registry)"
  type        = string
}

variable "frontend_image" {
  description = "Fully qualified image tag for the Streamlit frontend (e.g. from Artifact Registry)"
  type        = string
}