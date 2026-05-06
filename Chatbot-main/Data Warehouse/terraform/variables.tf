# common
variable "environment" {
  description = "Azure environment"
  type        = string
}


variable "data_location" {
  description = "Azure data_location name"
  type        = string
}

variable "location" {
  description = "Azure location"
  type        = string
}

# communication_email_service
variable "communication_email_name" {
  description = "Azure communication name"
  type        = string
}

# communication_service
variable "communication_name" {
  description = "Azure communication name"
  type        = string
}

# function_app
variable "app_name" {
  description = "Azure Function App name"
  type        = string
}

# key vault
variable "keyvault_name" {
  description = "Azure Key Vault name"
  type        = string
}

variable "keyvault_sku_name" {
  description = "Azure Key Vault sku name"
  type        = string
}

variable "tenant_id" {
  description = "Azure tenant_id"
  type        = string
}

# postgres server
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

# postgres server db
variable "pg_flexible_server_db" {
  description = "pg_flexible_server_dbname"
  type        = string
}

# private_dns_zone
variable "private_dns_zone_name" {
  description = "Name of the private DNS Zone"
  type        = string
}

# private_dns_zone_vnet
variable "private_dns_zone_vnet_link_name" {
  description = "Name of the private DNS Zone"
  type        = string
}

# resource_group
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

# service_plan
variable "service_plan_name" {
  description = "Azure service plan"
  type        = string
}

# storage_account
variable "storage_account_name" {
  description = "The name of the storage account."
  type        = string
}

variable "account_tier" {
  description = "The performance tier of the storage account (Standard or Premium)."
  type        = string
}

variable "account_replication_type" {
  description = "The replication type of the storage account (LRS, GRS, RAGRS, or ZRS)."
  type        = string
}

# subnet
variable "subnet_name" {
  description = "Name of the Subnet"
  type        = string
}

variable "subnet_address_prefixes" {
  description = "Address prefixes for the Subnet"
  type        = list(string)
}

variable "subnet_delegation_name" {
  description = "Name of the subnet_delegation"
  type        = string
}

#vnet
variable "vnet_name" {
  description = "Name of the Virtual Network"
  type        = string
}

variable "vnet_address_space" {
  description = "Address space for the Virtual Network"
  type        = list(string)
}

