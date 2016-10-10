#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

if [ ! -d .virtualenv ]; then
    virtualenv .virtualenv --no-site-packages
fi
source .virtualenv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

cd playbooks
ansible-galaxy install -r requirements.yml
ssh-add
ansible-playbook deploy.yml "$@"
