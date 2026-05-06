output "output_storage_account_name" {
  value = azurerm_storage_account.azurerm_storage_account.name
}

output "output_storage_account_primary_access_key" {
  value = azurerm_storage_account.azurerm_storage_account.primary_access_key
}