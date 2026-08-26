#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "usage: report-dataops.sh <status> <event-type> [failed-stage]" >&2
  exit 64
fi

: "${DATAOPS_URL:?set DATAOPS_URL}"
: "${GITHUB_RUN_ID:?missing GITHUB_RUN_ID}"
: "${GITHUB_RUN_ATTEMPT:?missing GITHUB_RUN_ATTEMPT}"
: "${GITHUB_REPOSITORY:?missing GITHUB_REPOSITORY}"
: "${GITHUB_SHA:?missing GITHUB_SHA}"
: "${GITHUB_REF_NAME:?missing GITHUB_REF_NAME}"

STATUS="$1"
EVENT_TYPE="$2"
FAILED_STAGE="${3:-}"
EVENT_ID="github:${GITHUB_RUN_ID}:${GITHUB_RUN_ATTEMPT}:${EVENT_TYPE}"

payload="$({
  jq --null-input \
    --arg event_id "${EVENT_ID}" \
    --arg event_type "${EVENT_TYPE}" \
    --arg occurred_at "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --arg project_ref "${GITHUB_REPOSITORY}" \
    --arg external_run_id "${GITHUB_RUN_ID}" \
    --argjson attempt "${GITHUB_RUN_ATTEMPT}" \
    --arg commit_sha "${GITHUB_SHA}" \
    --arg branch "${GITHUB_REF_NAME}" \
    --arg status "${STATUS}" \
    --arg failed_stage "${FAILED_STAGE}" \
    '{
      event_id: $event_id,
      event_type: $event_type,
      occurred_at: $occurred_at,
      provider: "github",
      project_ref: $project_ref,
      external_run_id: $external_run_id,
      attempt: $attempt,
      commit_sha: $commit_sha,
      branch: $branch,
      status: $status
    } + if $failed_stage == "" then {} else {failed_stage: $failed_stage} end'
})"

curl --fail --silent --show-error \
  --header "Content-Type: application/json" \
  --data "${payload}" \
  "${DATAOPS_URL}/api/v1/events/pipeline"
echo
