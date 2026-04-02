#!/bin/bash

# Port forward both databases in parallel
kubectl port-forward svc/mysql 33066:3306 -n sentinelsql &
kubectl port-forward svc/postgres 54322:5432 -n sentinelsql &

echo "Port forwarding started:"
echo "  MySQL:    localhost:33066"
echo "  Postgres: localhost:54322"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill 0" EXIT
wait
