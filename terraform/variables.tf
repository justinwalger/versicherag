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

variable "gemini_api_key" {
  description = "Gemini API key for the FastAPI backend's Settings (required, no default)"
  type        = string
  sensitive   = true
}

variable "qdrant_host" {
  description = "Qdrant Cloud endpoint URL for the FastAPI backend's Settings (required, no default)"
  type        = string
}

variable "qdrant_api_key" {
  description = "Qdrant Cloud API key for the FastAPI backend's Settings (required, no default)"
  type        = string
  sensitive   = true
}