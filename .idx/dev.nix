{ pkgs, ... }: {
  channel = "stable-23.11";

  packages = [
    pkgs.docker-compose
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
    pkgs.nodejs_20
    pkgs.git
    # REMOVE postgresql_15 and redis - Docker handles these!
  ];

  # THIS IS THE MAGIC LINE - Enable Docker service
  services.docker.enable = true;

  env = {};

  idx = {
    extensions = [
      "ms-python.python"
      "ms-python.vscode-pylance"
      "ms-azuretools.vscode-docker"  # Added Docker extension
      "bungcip.better-toml"
      "GitHub.copilot"
      "eamodio.gitlens"
    ];

    previews = {
      enable = true;
      previews = {
        backend = {
          command = [
            "bash" "-c" 
            "cd backend && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port $PORT"
          ];
          manager = "web";
        };
      };
    };

    workspace = {
      onCreate = {
        create-venv = "cd backend && python -m venv venv";
        install-deps = "cd backend && source venv/bin/activate && pip install -r requirements.txt";
        # REMOVE setup-postgres and setup-redis - Docker handles this
      };
      
      onStart = {
        # Start Docker services
        start-docker = "cd ~/attendance-system && docker-compose up -d";
        run-migrations = "cd backend && source venv/bin/activate && alembic upgrade head";
      };
    };
  };
} 
