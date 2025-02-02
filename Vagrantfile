# -*- mode: ruby -*-
# vi: set ft=ruby :
TERRAFORM_VERSION = "1.2.3"

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.env.enable # Enable vagrant-env(.env)
  config.vm.network "forwarded_port", guest: 8888, host: 8888
  config.vm.synced_folder ENV['HOME'], "/root"
  config.vm.synced_folder "./", "/opt/tfe-tools"
  config.vm.provision "shell", inline: <<-SHELL
    apt-get update 
    apt-get install -y python3 python3-pip unzip git curl
    git clone https://github.com/tfutils/tfenv.git ~/.tfenv
    ln -s ~/.tfenv/bin/* /usr/local/bin
    /usr/local/bin/tfenv install #{TERRAFORM_VERSION}
    /usr/local/bin/tfenv use #{TERRAFORM_VERSION}
    DEBIAN_FRONTEND=noninteractive apt-get install -y jupyter-notebook
    apt install -y zsh
    cd /opt/tfe-tools/nit-pytfe-core; python3 setup.py install
    cd /opt/tfe-tools/nit-pytfe-core; pip install -r requirements.txt
    cd /opt/tfe-tools/; pip install -r requirements.txt
  SHELL
end
