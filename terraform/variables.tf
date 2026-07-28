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

variable "langsmith_api_key" {
  description = "LangSmith API key for tracing the FastAPI backend's LangChain/LangGraph agent runs (required, no default)"
  type        = string
  sensitive   = true
}

variable "langsmith_project" {
  description = "LangSmith project name traces are grouped under"
  type        = string
  default     = "versicherag"
}

variable "langsmith_endpoint" {
  description = "LangSmith API endpoint"
  type        = string
  default     = "https://api.smith.langchain.com"
}

variable "langsmith_tracing" {
  description = "\"true\" to enable LangSmith tracing, \"false\" to disable without removing the key"
  type        = string
  default     = "true"
}