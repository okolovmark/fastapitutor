#!/bin/bash

# https://github.com/haris-musa/excel-mcp-server
source .env
NIX_DEVELOP_Q_AGENT=1 nix develop -c .venv/bin/excel-mcp-server stdio
