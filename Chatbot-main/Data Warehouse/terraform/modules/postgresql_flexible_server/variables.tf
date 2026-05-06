variable "location" {
  description = "Azure location"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "postgres_dbserver_name" {
  description = "PostgreSQL database server name"
  type        = string
}

variable "postgres_version" {
  description = "Database admin password"
  type        = string
}

variable "postgres_admin_user" {
  description = "Database admin username"
  type        = string
}

variable "postgres_admin_password" {
  description = "Database admin password"
  type        = string
}


variable "postgres_storage_mb" {
  description = "PostgreSQL storage mb"
  type        = number
}

variable "postgres_sku_name" {
  description = "PostgreSQL sku name"
  type        = string
}

variable "delegated_subnet_id" {
  description = "delegated_subnet_id"
  type        = string
}

variable "private_dns_zone_id" {
  description = "private_dns_zone_id"
  type        = string
}



