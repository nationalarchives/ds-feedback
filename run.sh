#!/bin/bash
set -euo pipefail

poetry install --only dev-app
tna-run config.wsgi:application
