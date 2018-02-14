#!/usr/bin/env bash

cd $(dirname $0)
ansible-galaxy install williamyeh.prometheus
ansible-galaxy install ansiblebit.grafana
sudo cp ansible_hosts /etc/ansible/hosts
ansible-playbook -b "$@" site.yml
