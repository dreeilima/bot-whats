#!/bin/bash

# Inicia o container Docker
docker-compose up -d

# Aguarda o container iniciar
sleep 10

# Inicia o monitor
python -m app.services.monitor 