ARG IMAGE=ghcr.io/nationalarchives/tna-python
ARG IMAGE_TAG=latest

FROM "$IMAGE":"$IMAGE_TAG"

# Ensure build/install steps run with sufficient permissions
USER root

ENV NPM_BUILD_COMMAND=compile
ARG BUILD_VERSION
ENV BUILD_VERSION="$BUILD_VERSION"

# Copy in the application code
COPY . .

# Install dependencies
RUN tna-build

# Copy in the static assets from TNA Frontend, collect static files and remove source files
RUN mkdir -p /app/app/static/assets; \
    cp -r /app/node_modules/@nationalarchives/frontend/nationalarchives/assets/* /app/app/static/assets; \
    poetry run python /app/manage.py collectstatic --no-input --clear; \
    rm -fR /app/src

# Clean up build dependencies
RUN tna-clean

# Allow non-root runtime user to update npm/node metadata in home directory
RUN mkdir -p /home/app/.npm && chown -R app:app /home/app/.nvm /home/app/.npm

# Run as non-root user
USER app

# Run the application
CMD ["tna-wsgi", "config.wsgi:application"]
