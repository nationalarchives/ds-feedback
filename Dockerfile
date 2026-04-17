ARG IMAGE=ghcr.io/nationalarchives/tna-python
ARG IMAGE_TAG=latest

FROM "$IMAGE":"$IMAGE_TAG"

ENV NPM_BUILD_COMMAND=compile
ARG BUILD_VERSION
ENV BUILD_VERSION="$BUILD_VERSION"

# Copy in the application code
COPY --chown=app . .

# Install dependencies
RUN tna-build

# Copy in the static assets from TNA Frontend, collect static files and remove source files
RUN mkdir -p /app/app/static/assets; \
    cp -r /app/node_modules/@nationalarchives/frontend/nationalarchives/assets/* /app/app/static/assets; \
    poetry run python /app/manage.py collectstatic --no-input --clear; \
    rm -fR /app/src

# Clean up build dependencies
RUN tna-clean

# Run the application
CMD ["tna-wsgi", "config.wsgi:application"]
