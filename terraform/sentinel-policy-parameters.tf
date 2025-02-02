data "tfe_policy_set" "config_stash" {
  name         = "tfe-tools"
  organization = "clover"
}

resource "tfe_policy_set_parameter" "managed_zones" {
  key           = "managed_zones"
  value         = file(var.managed_zones)
  policy_set_id = data.tfe_policy_set.config_stash.id
}