#!/bin/sh
set -e
WORKDIR="${SANDBOX_WORKSPACE:-/work}"
COMPOSE_DIR="${WORKDIR}/snmp"
COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.yaml"

usage() {
    echo "SNMP sandbox CLI (controls host Docker via socket)."
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "  up, start          Build/start SNMP simulators + Datadog Agent (default)"
    echo "  down, stop, destroy  Stop and remove the stack"
    echo "  pull               Pull simulator/agent images"
    echo "  ps                 docker compose ps"
    echo "  logs [args]        docker compose logs"
    echo "  compose <args>     Pass through to docker compose (from ${COMPOSE_DIR})"
    echo ""
    echo "Requires DD_API_KEY in the environment or in snmp/.env for 'up'."
}

have_api_key() {
    if [ -n "${DD_API_KEY:-}" ]; then
        return 0
    fi
    if [ -f "${COMPOSE_DIR}/.env" ]; then
        # Non-empty DD_API_KEY= value
        if grep -q '^DD_API_KEY=[^[:space:]]' "${COMPOSE_DIR}/.env" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

cd "${COMPOSE_DIR}"

cmd="${1:-up}"
if [ "$#" -gt 0 ]; then
    shift
fi

case "$cmd" in
    up|start)
        if ! have_api_key; then
            echo "DD_API_KEY is not set. Export it or add it to snmp/.env (copy from snmp/.env.example)." >&2
            exit 1
        fi
        mkdir -p "${WORKDIR}/tcpdump"
        exec docker compose -f "${COMPOSE_FILE}" up --build --force-recreate -d "$@"
        ;;
    down|destroy|stop)
        exec docker compose -f "${COMPOSE_FILE}" down --remove-orphans "$@"
        ;;
    pull)
        exec docker compose -f "${COMPOSE_FILE}" pull "$@"
        ;;
    ps)
        exec docker compose -f "${COMPOSE_FILE}" ps "$@"
        ;;
    logs)
        exec docker compose -f "${COMPOSE_FILE}" logs "$@"
        ;;
    compose)
        exec docker compose -f "${COMPOSE_FILE}" "$@"
        ;;
    help|-h|--help)
        usage
        exit 0
        ;;
    *)
        exec docker compose -f "${COMPOSE_FILE}" "$cmd" "$@"
        ;;
esac
