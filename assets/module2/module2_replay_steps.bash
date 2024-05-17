#!/usr/bin/env bash
## Prevent this script from being sourced
#shellcheck disable=SC2317
return 0  2>/dev/null || :

# shellcheck disable=SC2128
script_name=$(basename "$0")
#shellcheck disable=SC2128,SC2034
script_dir=$(dirname "$(readlink --canonicalize --no-newline "$0")")
source "$script_dir/../common/common_bash_libs"
#shellcheck disable=SC1091
source "$HOME/.labenv_custom.bash"

# Check that module1 steps replay has been done
check_module1_replay_steps() {
  [[ -f "$HOME/.config/cnd/.module1_replay_steps.done" ]] || {
    no_warn=1 "$script_dir/../module1/module1_replay_steps.bash"
  }
}

## Copy the Docker assets to the app dir
set_docker_assets_and_deps() {
  info "Copying Docker assets and basic app dependencies..."
  local -r cp_source="$script_dir"
  cp -- "$cp_source/Dockerfile" \
    "$cp_source/.dockerignore" \
    "$cp_source/requirements.txt" \
    "$script_dir/../../myfirstapp"
}

## Set GCP services
create_gcp_services() {
  info "Creating necessary GCP services..."
  gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    --quiet 2>/dev/null
  #shellcheck disable=SC2153
  # Variable should be comming from the environment, checked with cloudshell_bootstrap.bash
  gcloud artifacts repositories create cloud-run-source-deploy \
    --location="$region" \
    --repository-format=docker \
    --quiet
}

## Deploy the app to Cloud Run
deploy_to_cloudrun() {
  pushd "$script_dir/../../myfirstapp" || { error "Failed to move to dir $script_dir/../../myfirstapp. Exiting"; exit 1; }
  gcloud run deploy myfirstapp \
  --source . --allow-unauthenticated \
  --set-env-vars="NAME=CND" \
  --quiet
  popd || exit 1
}

wrap_up() {
  info "Registering successful replay of module 2 steps..."
  local -r registry_dir="$HOME/.config/cnd"
  mkdir -p "$registry_dir"
  touch "$registry_dir/.module2_replay_steps.done"
  [[ $no_warn ]] || {
    printfx "--------------------------------------------------------"
    warning "You must run \"source \$HOME/.bashrc\" before continuing"
    printfx "--------------------------------------------------------"
  }
}

main() {
  check_basic_requirements
  info "Replaying Module 1 steps..."
  check_module1_replay_steps
  info "Replaying Module 2 steps..."
  set_docker_assets_and_deps
  create_gcp_services
  deploy_to_cloudrun
  wrap_up
}

main "$@"