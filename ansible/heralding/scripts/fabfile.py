# this fabfile prepares an host to be managed by Ansible
# Usage:
#   fab -H X.Y.Z.P bootstrap

import os
import yaml
import jinja2

from fabric.api import *
from fabric.contrib.files import exists, contains, sed

def install_ansible():
    sudo('apt-get -y update')
    sudo('apt-get -y install software-properties-common')
    sudo('apt-get -y install python-pip python-setuptools python-dev')
    sudo('pip install ansible')

def _addpublickey(pub_key):
    run('echo "{0}" >> ~/.ssh/authorized_keys'.format(pub_key))
    run('chmod 600 ~/.ssh/authorized_keys')

def copypublickey():
    if os.path.isfile(os.path.expanduser('~/.ssh/id_rsa.pub')):
        pub_key = open(os.path.expanduser('~/.ssh/id_rsa.pub')).read()
        if not exists('~/.ssh'):
            run('mkdir -p ~/.ssh/')
            run('chmod 700 ~/.ssh/')
        if exists('~/.ssh/authorized_keys'):
            if not contains('~/.ssh/authorized_keys', pub_key.split(' ')[1]):
                _addpublickey(pub_key)
        else:
            _addpublickey(pub_key)

def change_ssh_port():
    sed('/etc/ssh/sshd_config', "Port 22", "Port 38512", use_sudo=True)
    sudo('service ssh restart')

def bootstrap():
    copypublickey()
    install_ansible()
    change_ssh_port()
