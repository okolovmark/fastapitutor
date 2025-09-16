{
  description = "FastAPI demo project dev with Python 3.13.5, PostgreSQL 15";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, nixpkgs-python, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python313 = nixpkgs-python.packages.${system}."3.13.5";

        commonDeps = [
          python313
          pkgs.pkg-config
          pkgs.git

          pkgs.postgresql_15
          pkgs.postgresql_15.dev
          pkgs.postgresql_15.pg_config
          pkgs.awscli2
          pkgs.nginx
          pkgs.ccze
          pkgs.go
        ];

        # nix run
        setupScript = pkgs.writeShellApplication {
          name = "fastapi-demo-setup";
          runtimeInputs = commonDeps;
          text = ''
            # Generate .env file if it doesn't exist
            if [ ! -f .env ]; then
              echo "📝 .env file not found. Let's create one!"
              echo

              read -r -p "PostgreSQL port (default: 5432): " pgport
              pgport=''${pgport:-5432}

              read -r -p "PostgreSQL user (default: fastapi): " pguser
              pguser=''${pguser:-fastapi}

              read -r -s -p "PostgreSQL password (default: fastapi): " pgpassword
              pgpassword=''${pgpassword:-fastapi}
              echo

              read -r -p "PostgreSQL database name (default: develop): " pgdatabase
              pgdatabase=''${pgdatabase:-develop}

              read -r -p "FastAPI port (default: 8000): " fastapi_port
              fastapi_port=''${fastapi_port:-8000}

              read -r -p "Nginx port (default: 80): " nginx_port
              nginx_port=''${nginx_port:-80}

              read -r -p "Github token (how to generate check in general README): " github_token
              github_token=''${github_token:-}
              {
                printf "PGPORT=%s\n" "$pgport"
                printf "PGUSER=%s\n" "$pguser"
                printf "PGPASSWORD=%s\n" "$pgpassword"
                printf "PGDATABASE=%s\n" "$pgdatabase"
                printf "FASTAPI_PORT=%s\n" "$fastapi_port"
                printf "NGINX_PORT=%s\n" "$nginx_port"
                printf "GITHUB_PERSONAL_ACCESS_TOKEN=%s\n" "$github_token"
              } > .env
              echo
              echo "✅ .env file created successfully!"
              echo
            fi

            # Load environment variables from .env file
            if [ -f .env ]; then
              set -a
              # shellcheck disable=SC1091
              source .env
              set +a
            fi

            # Setup PostgreSQL
            export PGDATA="$PWD/.postgres"
            export PGHOST="$PWD/.postgres"

            # Initialize PostgreSQL if needed
            if [ ! -d "$PGDATA" ]; then
              echo "Initializing PostgreSQL database in $PGDATA"
              initdb --auth=trust --no-locale --encoding=UTF8
              {
                echo "unix_socket_directories = '$PGHOST'"
                echo "log_destination = 'stderr'"
                echo "logging_collector = on"
                echo "log_directory = 'log'"
                echo "log_filename = 'postgresql.log'"
                echo "log_statement = 'all'"
                echo "listen_addresses = '*'"
              } >> "$PGDATA/postgresql.conf"
              echo "host    all             all             10.0.0.0/8              trust" >> "$PGDATA/pg_hba.conf"
              mkdir -p "$PGDATA/log"
            fi

            # Create and setup Python 3.13.5 virtual environment
            if [ ! -d .venv ]; then
              echo "Creating .venv for FastAPI..."
              python3.13 -m venv .venv
              # shellcheck disable=SC1091
              source .venv/bin/activate
              echo "Installing FastAPI dependencies..."
              python3.13 -m pip install "postgres-mcp" "excel-mcp-server" "requests" "fastapi[standard]"
              echo "Virtual environment setup for python 3.13.5 complete"
              deactivate
            fi

            # Create nix wrapper for python for Pycharm debug
            printf '#!/bin/bash\nNIX_DEVELOP_Q_AGENT=1 nix develop %s --command python "$@"\n' "$PWD" > "$PWD/nix-python.sh" && chmod +x "$PWD/nix-python.sh"

            # shellcheck disable=SC1091
            source .venv/bin/activate
            # Generate Nginx configuration file
            python scripts/generate_nginx_conf.py
            deactivate

            # MCP servers setup
            if [ ! -d "$PWD/.mcp-servers" ]; then
              mkdir -p "$PWD/.mcp-servers"
            fi

            # Build mcp server for github
            if [ ! -f "$PWD/.mcp-servers/github-mcp-server" ]; then
              echo "Building GitHub MCP server repository..."
              cd .tools/github-mcp-server && go build -o ../../.mcp-servers/github-mcp-server ./cmd/github-mcp-server && cd ../..
            fi

            echo "✅ FastAPI development environment setup complete!"
            echo "Run 'nix develop' to enter the development shell"
          '';
        };
      in
      {
        # One-time setup package
        packages.default = setupScript;

        # App that can be run with 'nix run'
        apps.default = {
          type = "app";
          program = "${setupScript}/bin/fastapi-demo-setup";
        };

        # nix develop
        devShells.default = pkgs.mkShell {
          name = "fastapi-devshell";
          buildInputs = commonDeps;
          shellHook = ''
            # Load environment variables from .env file
            if [ -f .env ]; then
              set -a
              source .env
              set +a
            fi

            # Setup PostgreSQL environment variables
            export PGDATA=$PWD/.postgres
            export PGHOST=$PWD/.postgres

            # Activate virtual environment if it exists
            if [ -d .venv ]; then
              source .venv/bin/activate
            else
              [ "$NIX_DEVELOP_Q_AGENT" != "1" ] && echo "⚠️ Virtual environment for python 3.13.5 not found. Run 'nix run' first to set up the environment."
            fi

            function pg_start() {
              if [ -d "$PGDATA" ]; then
                pg_ctl start -o "-k $PGHOST" || echo "PostgreSQL already running"
              else
                echo "⚠️ PostgreSQL not initialized. Run 'nix run' first to set up the environment."
              fi
            }

            function pg_stop() {
              if [ -d "$PGDATA" ]; then
                echo "Stopping PostgreSQL..."
                pg_ctl stop
                echo "PostgreSQL stopped"
              fi
            }

            function pg_logs() {
              if [ -f "$PGDATA/log/postgresql.log" ]; then
                tail -f "$PGDATA/log/postgresql.log" | ccze -A
              else
                echo "PostgreSQL log file not found at $PGDATA/log/postgresql.log"
              fi
            }

            function nginx_start() {
              echo "Starting Nginx with custom configuration..."
              mkdir -p "$PWD/.nginx/logs"
              if nginx -c "$PWD/.nginx/nginx.conf" -p "$PWD/.nginx" -e "$PWD/.nginx/logs/error.log"; then
                echo "Nginx started. Access at http://localhost:$NGINX_PORT"
              else
                echo "Failed to start Nginx. Check logs at $PWD/.nginx/logs/error.log"
              fi
            }

            function nginx_stop() {
              echo "Stopping Nginx..."
              if nginx -c "$PWD/.nginx/nginx.conf" -p "$PWD/.nginx" -e "$PWD/.nginx/logs/error.log" -s stop; then
                echo "Nginx stopped"
              else
                echo "Nginx was not running"
              fi
            }

            function nginx_reload() {
              echo "Reloading Nginx configuration..."
              if nginx -c "$PWD/.nginx/nginx.conf" -p "$PWD/.nginx" -e "$PWD/.nginx/logs/error.log" -s reload; then
                echo "Nginx configuration reloaded"
              else
                echo "Failed to reload Nginx. Is it running?"
              fi
            }

            function all_start() {
              echo "Starting all services..."
              pg_start
              nginx_start
              echo "All services started"
            }

            function q_chat() {
                q chat --agent fastapi-demo
            }

            function welcome_message() {
              echo -e "\n\033[1;36m╔══════════════════════════════════════════════════════════════╗\033[0m"
              echo -e "\033[1;36m║                    🚀 FastAPI DEV ENVIRONMENT                ║\033[0m"
              echo -e "\033[1;36m╚══════════════════════════════════════════════════════════════╝\033[0m\n"

              echo -e "\033[1;33m📋 System Information:\033[0m"
              echo -e "  🐍 Python: $(python --version | cut -d' ' -f2)"
              echo -e "  🐘 PostgreSQL: $(psql --version | cut -d' ' -f3)"
              echo -e "  🌐 Nginx:      $(nginx -v 2>&1 | awk -F/ '{print $2}')"

              echo -e "\n\033[1;34m🗄️  Database Commands:\033[0m"
              echo -e "  🔗 psql <db_name>    - Connect to PostgreSQL"
              echo -e "  📊 pg_logs           - View PostgreSQL logs (live)"
              echo -e "  ▶️ pg_start          - Start PostgreSQL localserver"
              echo -e "  ⏹️ pg_stop           - Stop PostgreSQL localserver"
              echo -e "  🔄 backup_restore    - Will download and restore the latest backup"

              echo -e "\n\033[1;32m🌐 Nginx Commands:\033[0m"
              echo -e "  🚀 nginx_start       - Start Nginx server"
              echo -e "  🛑 nginx_stop        - Stop Nginx server"
              echo -e "  🔄 nginx_reload      - Reload Nginx config"

              echo -e "\n\033[1;36m🔌 MCPs:\033[0m Use Amazon Q CLI for database, github actions, excel file generation"
              echo -e "  🚀 q_chat            - Run Q CLI with current environment"

              echo -e "\n  🚀 all_start         - Start all services (Postgres, Nginx)"

              echo -e "\n\033[1;37m💡 Tip: You can find the implementation of these functions in the devShells.default variable in the flake.nix file\033[0m"
              echo -e "\033[1;37m💡 Tip: Use 'welcome_message' to show this help again\033[0m\n"
            }

            [ "$NIX_DEVELOP_Q_AGENT" != "1" ] && welcome_message

            # Cleanup function to stop PostgreSQL, Odoo, Nginx when exiting the shell
            cleanup() {
              nginx_stop
              pg_stop
            }
            trap cleanup EXIT
          '';
        };
      }
    );
}
