terraform {
  cloud {
    hostname     = "terraform.example.com"
    organization = "example"

    workspaces {
      name = "tfe-tools"
    }
  }
}
