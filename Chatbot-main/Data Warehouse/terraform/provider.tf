terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0.0"
    }
  }
}

provider "azurerm" {
  subscription_id = "cb4efa9d-9e95-4dbd-b4f9-908d51482781"
  tenant_id       = "04c70eb4-8f26-4807-9934-e02e89266ad0"
  features {}
}
