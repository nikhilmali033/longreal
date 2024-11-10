#!/bin/bash

# Exit on error
set -e

echo "Starting Python environment setup..."

# Update system and install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install pyenv
echo "Installing pyenv..."
curl https://pyenv.run | bash

# Add pyenv to PATH
echo "Configuring pyenv..."
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Load new shell configuration
echo "Reloading shell configuration..."
source ~/.bashrc

# Install Python 3.11.5 (change this version if needed)
echo "Installing Python 3.11.5..."
$HOME/.pyenv/bin/pyenv install 3.11.5

# Set as global version
echo "Setting Python 3.11.5 as global version..."
$HOME/.pyenv/bin/pyenv global 3.11.5

echo "Setup complete! Please restart your terminal."
echo "After restarting, verify installation with:"
echo "python --version"
echo "pip --version"