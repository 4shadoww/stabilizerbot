#!/bin/bash

# Set time zone
export TZ="/usr/share/zoneinfo/Europe/Helsinki"

# Set locale
export LANGUAGE="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"
export PYTHONIOENCODING="UTF-8"

# Load virtual env
source /data/project/stabilizerbot/virtualenv/bin/activate

# Start yunomi
YUNOMI="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/stabilizer.py"
$YUNOMI
