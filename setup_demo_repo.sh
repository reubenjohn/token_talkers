#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <destination_folder>"
    exit 1
fi

# Assign the first argument to a variable
DEST_FOLDER=$1

mkdir -p "$DEST_FOLDER"
cd "$DEST_FOLDER"

# Clone the repository into the specified folder
git clone https://github.com/psf/requests.git

# Check if the clone operation was successful
if [ $? -ne 0 ]; then
    echo "Failed to clone the repository."
    exit 1
fi

