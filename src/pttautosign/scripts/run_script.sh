#!/bin/bash

# Activate virtual environment if it exists
if [ -f "$HOME/.poetry/env" ]; then
    source "$HOME/.poetry/env"
fi

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the application
pttautosign run

# Log the execution
echo "$(date): PTT Auto Sign executed" >> "$DIR/execution.log" 