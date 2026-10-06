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

variable "app_password" {
  description = "Shared password gating the /api/chat endpoint, for the FastAPI backend's Settings (required, no default)"
  type        = string
  sensitive   = true
}

variable "langfuse_public_key" {
  description = "Langfuse public key for tracing the FastAPI backend's LangChain/LangGraph agent runs"
  type        = string
  default     = ""
}

variable "langfuse_secret_key" {
  description = "Langfuse secret key for tracing the FastAPI backend's LangChain/LangGraph agent runs"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_base_url" {
  description = "Langfuse API endpoint"
  type        = string
  default     = "https://cloud.langfuse.com"
}

variable "langfuse_tracing" {
  description = "\"true\" to enable Langfuse tracing, \"false\" to disable without removing the keys"
  type        = string
  default     = "false"
}