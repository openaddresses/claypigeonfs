#!/bin/bash -e
#
# Install the chef ruby gem if chef-solo is not in the path.
# This script is safe to run multiple times.
#
if [ ! `which chef-solo` ]; then
    # Suppress chef_server_url prompt with hint from
    # http://unix.stackexchange.com/questions/106552/apt-get-install-without-debconf-prompt
    DEBIAN_FRONTEND=noninteractive apt-get install -y chef
fi

cd `dirname $0`
chef-solo -c $PWD/solo.rb -j $PWD/role.json

