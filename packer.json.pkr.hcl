
variable "base_image" {
  type    = string
  default = "ubuntu:latest"
}

variable "home" {
  type    = string
  default = "${env("HOME")}"
}

variable "pwd" {
  type    = string
  default = "${env("PWD")}"
}

variable "repo" {
  type    = string
  default = "tfe-tools"
}

variable "terraform_version" {
  type    = string
  default = "1.2.3"
}

variable github_login {
  type = string
  default = "${env("GITHUB_LOGIN")}"
}

variable github_token {
  type = string
  default = "${env("GITHUB_TOKEN")}"
}

variable github_user {
  type = string
  default = "${env("GITHUB_USER")}"
}

source "docker" "tfe-tools" {
  commit = true
  image  = "${var.base_image}"
  changes = [
    "ENV GITHUB_TOKEN=${var.github_token}",
    "ENV GITHUB_LOGIN=${var.github_login}",
    "ENV GITHUB_USER=${var.github_user}",
    "ENTRYPOINT /usr/bin/jupyter-notebook --allow-root --ip 0.0.0.0 --notebook-dir=/opt/tfe-tools/"
  ]
}

build {
  sources = ["source.docker.tfe-tools"]

  provisioner "file" {
    destination = "/opt/tfe-tools/"
    source      = "${var.pwd}/"
  }

  provisioner "shell" {
    inline = [
      "mkdir -p /root/.terraform.d/",
      "mkdir /root/.ssh"
    ]
  }

  provisioner "file" {
    destination = "/root/"
    source      = "${var.home}/.terraform.d/credentials.tfrc.json"
  }

  provisioner "file" {
    destination = "/root/.zshrc"
    source      = "${var.home}/.zshrc"
  }

  provisioner "file" {
    destination = "/root/.ssh"
    source      = "${var.home}/.ssh"
  }

  provisioner "shell" {
    inline = [
      "apt-get update", 
      "apt-get install -y python3 python3-pip unzip git curl", 
      "git clone https://github.com/tfutils/tfenv.git ~/.tfenv", 
      "ln -s ~/.tfenv/bin/* /usr/local/bin", "/usr/local/bin/tfenv install ${var.terraform_version}", 
      "/usr/local/bin/tfenv use ${var.terraform_version}",
      "DEBIAN_FRONTEND=noninteractive apt-get install -y jupyter-notebook",
      "apt install -y zsh",
      "cd /opt/tfe-tools/nit-pytfe-core; python3 setup.py install", 
      "cd /opt/tfe-tools/nit-pytfe-core; pip install -r requirements.txt", 
      "cd /opt/tfe-tools/; pip install -r requirements.txt"
    ]
  }

  post-processor "docker-tag" {
    repository = "${var.repo}"
    tag        = [
      "latest"
    ]
  }
}
