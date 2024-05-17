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
app_name="db-api"
app_dir="$script_dir/../../$app_name"

# Check that module1 steps replay has been done
check_module_replay_steps() {
  local -r module_name="$1"; shift
  [[ -f "$HOME/.config/cnd/.${module_name}_replay_steps.done" ]] || {
    no_warn=1 "$script_dir/../${module_name}/${module_name}_replay_steps.bash"
  }
}

## Prepare the app dir
prepare_app_dir() {
  info "Preparing the app dir..."
  mkdir -p "$app_dir/src"
}

## Copy the Docker assets to the app dir
copy_assets_and_deps() {
  info "Copying code assets and basic app dependencies..."
  local -r cp_source="$script_dir"
  declare -a files_to_copy=(
    "Dockerfile"
    "requirements.txt"
    ".dockerignore"
    ".labenv_db"
  )
  for file in "${files_to_copy[@]}"; do
    cp -- "$cp_source/$file" "$app_dir"
  done
  source "$app_dir/.labenv_db"
  declare -a files_to_copy_src=(
    "connect_connector.py"
    "base_logger.py"
    "app.py"
  )
  for file in "${files_to_copy_src[@]}"; do
    cp -- "$cp_source/$file" "$app_dir/src"
  done
  # Copy the templates dir
  cp -r -- "$cp_source/templates" "$app_dir/src"
}

## Set GCP services
create_gcp_services() {
  info "Creating database..."
  gcloud services enable \
    sqladmin.googleapis.com \
    --quiet 2>/dev/null
  info "Creating database instance..."
  gcloud sql instances create "$DB_INSTANCE" \
    --database-version=POSTGRES_14 \
    --tier=db-g1-small \
    --region="$region" \
    --quiet
  info "Setting up database password..."
  gcloud sql users set-password postgres \
    --instance="$DB_INSTANCE" \
    --password="$DB_PASS" \
    --quiet
  info "Creating database..."
  gcloud sql databases create "$DB_NAME" \
    --instance="$DB_INSTANCE" \
    --quiet
}

## Create Database
create_db() {
  info "Creating the TABS vs SPACES database..."
  pushd $app_dir || { error "Failed to move to dir $app_dir. Exiting"; exit 1; }
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  cp "$script_dir/create_db.py" "$app_dir/src"
  python src/create_db.py
  popd || exit 1
}

## Deploy the app to Cloud Run
deploy_to_cloudrun() {
  info "Deploying app $app_name to Cloud Run..."
  pushd "$app_dir" || { error "Failed to move to dir $app_dir. Exiting"; exit 1; }
  gcloud run deploy "$app_name" \
  --source . \
  --platform managed \
  --region "$region" \
  --allow-unauthenticated \
  --set-env-vars=INSTANCE_CONNECTION_NAME="$PROJECT_ID:$REGION:$DB_INSTANCE" \
  --set-env-vars=DB_NAME="$DB_NAME" \
  --set-env-vars=DB_USER="$DB_USER" \
  --set-env-vars=DB_PASS="$DB_PASS" \
  --async
  popd || exit 1
}

wrap_up() {
  info "Registering successful replay of module 3 steps..."
  local -r registry_dir="$HOME/.config/cnd"
  mkdir -p "$registry_dir"
  touch "$registry_dir/.module3_replay_steps.done"
  [[ $warn ]] && return 0
  printfx "--------------------------------------------------------"
  warning "You must run \"source \$HOME/.bashrc\" before continuing"
  printfx "--------------------------------------------------------"
}

main() {
  check_basic_requirements
  info "Checking Module 1 steps..."
  check_module_replay_steps module1
  info "Checking Module 2 steps..."
  check_module_replay_steps module2
  prepare_app_dir
  copy_assets_and_deps
  create_gcp_services
  create_db
  deploy_to_cloudrun
  wrap_up false
}

main "$@"