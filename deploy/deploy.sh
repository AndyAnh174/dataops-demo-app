#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: deploy.sh <web-image> <api-image> <revision>" >&2
  exit 64
fi

WEB_IMAGE="$1"
API_IMAGE="$2"
APP_REVISION="$3"
DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/dataops-demo/app}"
COMPOSE_FILE="${DEPLOY_ROOT}/compose.yaml"
ENV_FILE="${DEPLOY_ROOT}/app.env"
PREVIOUS_ENV_FILE="${DEPLOY_ROOT}/previous.env"

mkdir -p "${DEPLOY_ROOT}"
install -m 0644 compose.yaml "${COMPOSE_FILE}"
install -m 0644 Caddyfile "${DEPLOY_ROOT}/Caddyfile"

docker pull "${WEB_IMAGE}"
docker pull "${API_IMAGE}"

if [[ -f "${ENV_FILE}" ]]; then
  cp "${ENV_FILE}" "${PREVIOUS_ENV_FILE}"
fi

umask 077
printf 'WEB_IMAGE=%s\nAPI_IMAGE=%s\nAPP_REVISION=%s\n' \
  "${WEB_IMAGE}" "${API_IMAGE}" "${APP_REVISION}" > "${ENV_FILE}"

rollback() {
  local exit_code=$?
  trap - ERR
  if [[ -f "${PREVIOUS_ENV_FILE}" ]]; then
    echo "Deployment failed; restoring the previous immutable image set." >&2
    cp "${PREVIOUS_ENV_FILE}" "${ENV_FILE}"
    docker compose --project-directory "${DEPLOY_ROOT}" \
      --env-file "${ENV_FILE}" --file "${COMPOSE_FILE}" \
      up --detach --remove-orphans --wait
  else
    echo "Initial deployment failed; no previous release exists yet." >&2
  fi
  exit "${exit_code}"
}
trap rollback ERR

docker compose --project-directory "${DEPLOY_ROOT}" \
  --env-file "${ENV_FILE}" --file "${COMPOSE_FILE}" \
  up --detach --remove-orphans --wait

curl --fail --silent --show-error --retry 8 --retry-delay 2 \
  http://127.0.0.1/api/health
echo
echo "Deployed revision ${APP_REVISION}."
