terraform {
  cloud {
    hostname     = "terraform.corp.clover.com"
    organization = "clover"

    workspaces {
      name = "tfe-tools"
    }
  }
}