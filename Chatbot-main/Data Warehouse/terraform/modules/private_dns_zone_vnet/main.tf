resource "azurerm_private_dns_zone_virtual_network_link" "azurerm_private_dns_zone_virtual_network_link" {
  name                  = var.private_dns_zone_vnet_link_name
  private_dns_zone_name = var.private_dns_zone_name
  virtual_network_id    = var.virtual_network_id
  resource_group_name   = var.resource_group_name
}