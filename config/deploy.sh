#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

if [ ! -d .virtualenv ]; then
    virtualenv .virtualenv --no-site-packages
fi
source .virtualenv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
ansible-playbook -i playbooks/inventory playbooks/deploy.yml -vvvv
