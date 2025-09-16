#!/bin/bash

# https://github.com/crystaldba/postgres-mcp
source .env
export DATABASE_URI="postgresql://${PGUSER}:${PGPASSWORD}@localhost:${PGPORT}/${PGDATABASE}"
NIX_DEVELOP_Q_AGENT=1 nix develop -c .venv/bin/postgres-mcp --access-mode=unrestricted
