#!/usr/bin/env bash
## Prevent this script from being sourced
#shellcheck disable=SC2317
return 0  2>/dev/null || :

# shellcheck disable=SC2128
script_name=$(basename "$0")
#shellcheck disable=SC2128,SC2034
script_dir=$(dirname "$(readlink --canonicalize --no-newline "$0")")
source "$script_dir/common_bash_libs"

# Configures a basic working Cloud Shell environment for Qwiklabs
configure_qw_cs() {
  local -r cs_source="https://raw.githubusercontent.com/javiercanadillas/qwiklabs-cloudshell-setup/main/setup_qw_cs"
  bash <(curl -s "$cs_source")
}

set_git_config() {
  info "Setting git config..."
  git config --global user.name "$USER" # env var containing the Qwiklabs user ID
  git config --global user.email "$USER@qwiklabs.net"
  git config --global init.defaultBranch main
}

wrap_up() {
  info "Registering successful bootstraping of module 1..."
  local -r registry_dir="$HOME/.config/cnd"
  mkdir -p "$registry_dir"
  touch "$registry_dir/.cloudshell_bootstrap.done"
}

main() {
  check_basic_requirements
  configure_qw_cs
  set_git_config
  wrap_up
}

main "$@"