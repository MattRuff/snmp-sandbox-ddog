#!/usr/bin/env bash
# Build the SNMP simulator image (all device data baked in) and push to Docker Hub.
#
# Prerequisites: docker login
# Usage:
#   export DOCKERHUB_USER=your-dockerhub-username
#   ./publish-dockerhub.sh
# Optional: IMAGE_NAME=snmp-sandbox-sim TAG=v1 ./publish-dockerhub.sh

set -euo pipefail

DOCKERHUB_USER="${DOCKERHUB_USER:?Set DOCKERHUB_USER to your Docker Hub username or organization}"
IMAGE_NAME="${IMAGE_NAME:-snmp-sandbox-sim}"
TAG="${TAG:-latest}"
FULL_IMAGE="${DOCKERHUB_USER}/${IMAGE_NAME}:${TAG}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Building ${FULL_IMAGE} from $(pwd) ..."
docker build -f Dockerfile.snmp_container -t "${FULL_IMAGE}" -t "snmp_container:local" .

echo "Pushing ${FULL_IMAGE} ..."
docker push "${FULL_IMAGE}"

echo ""
echo "Done. Pre-built workflow (no SNMP data bind-mount from host):"
echo "  export DD_API_KEY='<your_datadog_api_key>'   # required; not in any image"
echo "  export SNMP_SIM_IMAGE=${FULL_IMAGE}"
echo "  docker compose pull   # optional: pulls agent + your sim image if registry allows"
echo "  docker compose up -d --no-build"
