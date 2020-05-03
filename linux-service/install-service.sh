#! /bin/sh

sudo cp -rf psh-actor.service /usr/lib/systemd/system

sudo systemctl daemon-reload
sudo systemctl start psh-actor

sudo systemctl enable psh-actor
