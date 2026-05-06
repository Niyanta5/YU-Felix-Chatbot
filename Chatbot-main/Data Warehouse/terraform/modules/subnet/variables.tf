variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

# subnet
variable "subnet_name" {
  description = "Name of the Subnet"
  type        = string
}

variable "virtual_network_name" {
  description = "vnet name for the Subnet"
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