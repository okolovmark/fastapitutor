# FastAPI Development Rules

## Command Execution Requirements

When executing any bash commands using the `executeBash` tool:

1. **Use nix develop wrapper**: Always use prefix commands with `NIX_DEVELOP_Q_AGENT=1 nix develop -c` to ensure proper environment.

Example: `NIX_DEVELOP_Q_AGENT=1 nix develop -c bash -c "echo 'Testing quiet mode - this should be the only output'"`

### Example Command Pattern

Instead of: `python --version`  
Use: `nix develop -c python --version`

This ensures all commands run with the proper Nix environment configuration including PostgreSQL, Python 3.13.5, and all FastAPI dependencies.

## Environment

1. In `.nginx` you can find nginx configuration files.
2. In `.postgres` you can find PostgreSQL configuration files and data directory. logs are in `.postgres/logs`.
3. You must use MCP `postgres` tools to interact with the FastAPI database if you want to run any sql query. Database name you can find in `.env` file.
4. You must use MCP `github` tools to interact with the Kaertech repositories on GitHub.
5. You must use MCP `excel` tools when I request you to create excel file (dont write any scripts for it).

## Github behavior

### PR reviews

When you review a PR, you must consider next steps:

1. Code quality and adherence to best practices
2. Potential bugs or edge cases
3. Performance optimizations
4. Readability and maintainability
5. Any security concerns
6. Suggest improvements and explain your reasoning for each suggestion.
7. Suggest alternative approaches if you think they are better.

## Unit tests

When you write unit tests, you must include tests for:

1. Normal expected inputs
2. Edge cases
3. Invalid inputs
