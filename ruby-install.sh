#!/bin/bash

# -----------------------------------------------------------------------
# Installs Ruby 2.5 using rbenv/ruby-build on the Raspberry Pi (Raspbian)
#
# Run from the web:
#   bash <(curl -s raw_script_url_here)
# -----------------------------------------------------------------------

# Set up variables
bold="\033[1m"
normal="\033[0m"

# Welcome message
echo -e "\n${bold}This will install Ruby 2.5 using rbenv/ruby-build."
echo -e "It can take about 2 hours to compile on the Raspberry Pi.${normal}"

# Prompt to continue
read -p "  Continue? (y/n) " ans
if [[ $ans != "y" ]]; then
  echo -e "\nQuitting...\n"
  exit
fi
echo

# Time the install process
START_TIME=$SECONDS

# Check out rbenv into ~/.rbenv
git clone https://github.com/rbenv/rbenv.git ~/.rbenv

# Add ~/.rbenv/bin to $PATH, enable shims and autocompletion
read -d '' String <<"EOF"
# rbenv
export PATH="$HOME/.rbenv/bin:$PATH"
eval "$(rbenv init -)"
EOF

# For new shells
echo -e "\n${String}\n" >> ~/.bashrc

# For current shell
eval "${String}"

# Install ruby-build as an rbenv plugin, adds `rbenv install` command
git clone https://github.com/rbenv/ruby-build.git ~/.rbenv/plugins/ruby-build

# Install dependencies
#  See: https://github.com/rbenv/ruby-build/wiki#suggested-build-environment
sudo apt-get update
sudo apt-get install -y autoconf bison build-essential libssl-dev libyaml-dev libreadline6-dev zlib1g-dev libncurses5-dev libffi-dev libgdbm3 libgdbm-dev

# Install Ruby 2.5, don't generate RDoc to save lots of time
CONFIGURE_OPTS="--disable-install-doc --enable-shared" rbenv install 2.5.1 --verbose

# Set Ruby 2.5 as the global default
rbenv global 2.5.1

# Don't install docs for gems (saves lots of time)
echo -e "gem: --no-document" > ~/.gemrc

# Print the time elapsed
ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo -e "\n${bold}Finished in $(($ELAPSED_TIME/60/60)) hr, $(($ELAPSED_TIME/60%60)) min, and $(($ELAPSED_TIME%60)) sec${normal}\n"

