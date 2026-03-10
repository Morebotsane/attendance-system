#!/bin/bash

# Backend structure
mkdir -p backend/{app/{api/{endpoints,dependencies},core,models,schemas,services,db,utils},alembic/versions,tests/{unit,integration},scripts}
mkdir -p backend/app/storage/{photos,qr_codes,temp}

# Frontend structure
mkdir -p frontend/{public,src/{components/{common,attendance,admin,reports},pages,services,hooks,utils,contexts,assets/{images,styles}}}

# Docker and deployment
mkdir -p deployment/{docker,nginx}

# Documentation
mkdir -p docs/{api,user_guide,deployment}

# Root level files
touch README.md
touch .gitignore
touch docker-compose.yml
touch Makefile

echo "Project structure created successfully!"
