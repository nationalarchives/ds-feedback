ARG IMAGE=ghcr.io/nationalarchives/tna-python-django
ARG IMAGE_TAG=latest

FROM "$IMAGE":"$IMAGE_TAG"

ENV NPM_BUILD_COMMAND=compile
ARG BUILD_VERSION
ENV BUILD_VERSION="$BUILD_VERSION"

######################################################################
# UID/GID configuration for cross-platform development
#
# This section is primarily needed for Linux users running Docker Engine, where
# file permission issues can occur when mounting volumes. It sets the UID/GID
# for the 'app' user in the container to match the host system, preventing
# problems with file ownership.
#
# Docker Desktop and OrbStack users usually do not need to set these args, as
# their Docker implementations handle permissions differently.
#
# For more info, see README.md
######################################################################
USER root
ARG UID=1000
ARG GID=1000
ARG USERNAME=app
RUN usermod -u $UID $USERNAME && \
    groupmod -g $GID $USERNAME && \
    chown -R $UID:$GID /app /home/app
USER app

# Copy in the application code
COPY --chown=app . .

# Install dependencies
RUN tna-build

# Copy in the static assets from TNA Frontend
RUN mkdir /app/app/static/assets; \
    cp -r /app/node_modules/@nationalarchives/frontend/nationalarchives/assets/* /app/app/static/assets; \
    poetry run python /app/manage.py collectstatic --no-input --clear

# Delete source files, tests and docs
RUN rm -fR /app/src /app/test /app/docs

# Run the application
CMD ["tna-run", "config.wsgi:application"]
