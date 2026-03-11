{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-23.11"; # Or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.docker
    pkgs.docker-compose
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
    pkgs.nodejs_20
    pkgs.git
    pkgs.postgresql_15
    pkgs.redis
  ];

  # Sets environment variables in the workspace
  env = {
    # DATABASE_URL = "postgresql://localhost:5432/hospital";
  };

  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "ms-python.python"
      "ms-python.vscode-pylance"
      "bungcip.better-toml"
      "GitHub.copilot"
      "eamodio.gitlens"
    ];

    # Enable previews and customize configuration
    previews = {
      enable = true;
      previews = {
        # The key "backend" is the identifier - no need for an "id" field inside!
        backend = {
          command = [
            "bash" "-c" 
            "cd backend && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port $PORT"
          ];
          manager = "web";
          # Optionally specify the working directory
          # cwd = "backend";
        };
      };
    };

    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        # Create virtual environment
        create-venv = "cd backend && python -m venv venv";
        # Install dependencies
        install-deps = "cd backend && source venv/bin/activate && pip install -r requirements.txt";
        # Setup database services
        setup-postgres = "pg_ctl -D $HOME/postgres-data start || initdb $HOME/postgres-data -A trust && pg_ctl -D $HOME/postgres-data start";
        setup-redis = "redis-server --daemonize yes || true";
      };
      
      # Runs when the workspace is (re)started
      onStart = {
        # Start database services if not running
        start-postgres = "pg_ctl -D $HOME/postgres-data status || pg_ctl -D $HOME/postgres-data start";
        start-redis = "redis-cli ping || redis-server --daemonize yes";
        # Run migrations
        run-migrations = "cd backend && source venv/bin/activate && alembic upgrade head";
      };
    };
  };
}