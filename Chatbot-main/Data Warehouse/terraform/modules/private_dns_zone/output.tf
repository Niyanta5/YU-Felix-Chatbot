output "output_private_dns_name" {
  value = azurerm_private_dns_zone.azurerm_private_dns_zone.name
}

output "output_private_dns_id" {
  value = azurerm_private_dns_zone.azurerm_private_dns_zone.id
}