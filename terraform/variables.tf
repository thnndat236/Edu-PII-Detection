variable "project_id" {
  description = "project_id"
}

variable "region" {
  description = "region"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "zone" {
  description = "zone"
}

variable "cluster_node_count" {
  description = "number of nodes within the pool"
  default     = 1
}

variable "machine_type" {
  description = "machine type"
  default     = "e2-standard-2"
}

variable "ssh_key" {
  description = "Value of the SSH Key to access the instance"
  type        = string
}
