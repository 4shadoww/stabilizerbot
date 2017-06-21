#!/bin/bash
GRID="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/grid.sh"
jstart -mem 500m -N fiwiki $GRID
