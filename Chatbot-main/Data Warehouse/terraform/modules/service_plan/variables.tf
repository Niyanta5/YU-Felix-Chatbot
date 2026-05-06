variable "location" {
  description = "Azure location"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

# service plan
variable "service_plan_name" {
  description = "Azure service plan"
  type        = string
}
