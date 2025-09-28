# FastAPI Development Environment

This is a Nix-based development environment for FastAPI with Python 3.13 and PostgreSQL 15.
[Tutorial](https://fastapi.tiangolo.com/tutorial)

## First-time Setup

When you first clone this repository, run the one-time setup command:

```bash
# Run the setup script (initializes PostgreSQL, sets up venv)
nix run
```

In Pycharm in the right down corner select interpreter and select existing one: .venv/bin/python

In Pycharm in the left bar select project and click right button mouse on `src` and Mark directory as Sources Root

## Regular Development

After the initial setup, you can enter the development environment with:

```bash
# Enter the development shell
nix develop
```

## Re-installation

If you need to run the setup again or manually set up components:

```bash
# Run the setup script again
nix run
```

## Debug mode

To run FastAPI in debug mode, set `nix-python.sh` as the interpreter in PyCharm in the lower right corner (you may need to try several times). After open profile in right top corner, click edit and choose `nix-python.sh`

Add New Interpreter -> Add Local Interpreter -> Select Existing -> Select `nix-python.sh`.
