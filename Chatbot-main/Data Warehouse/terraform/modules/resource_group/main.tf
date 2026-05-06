resource "azurerm_resource_group" "azurerm_resource_group" {
  name     = var.resource_group_name
  location = var.location
}
