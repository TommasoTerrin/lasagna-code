#!/bin/bash
. "$(dirname "$0")/../_lib/project.sh"
shop_project
mkdir -p .lasagna/state
lasagna_init
