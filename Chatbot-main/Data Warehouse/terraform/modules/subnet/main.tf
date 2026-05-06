resource "azurerm_subnet" "azurerm_subnet" {
  name                 = var.subnet_name
  resource_group_name  = var.resource_group_name
  virtual_network_name = var.virtual_network_name 
  address_prefixes     = var.subnet_address_prefixes

  delegation {
    name = var.subnet_delegation_name
    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action"
      ]
    }
  }
}
