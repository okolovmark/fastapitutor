#!/bin/bash

# https://github.com/github/github-mcp-server?tab=readme-ov-file#build-from-source
source .env
export GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN}"
NIX_DEVELOP_Q_AGENT=1 nix develop -c .mcp-servers/github-mcp-server stdio
