resource "azurerm_postgresql_flexible_server_database" "azurerm_postgresql_flexible_server_database" {
  name      = var.pg_flexible_server_db
  server_id = var.pg_flexible_server_id
  collation = "en_US.utf8"
  charset   = "utf8"

  # prevent the possibility of accidental data loss
  lifecycle {
    prevent_destroy = true
  }
}




