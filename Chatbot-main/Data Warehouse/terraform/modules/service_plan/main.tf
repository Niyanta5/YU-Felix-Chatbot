resource "azurerm_app_service_plan" "azurerm_app_service_plan" {
  name                = var.service_plan_name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku {
    tier = "Standard"
    size = "S1"
  }
}
