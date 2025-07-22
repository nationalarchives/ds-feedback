ARG IMAGE=ghcr.io/nationalarchives/tna-python-django
ARG IMAGE_TAG=latest

FROM "$IMAGE":"$IMAGE_TAG"

ENV NPM_BUILD_COMMAND=compile
ARG BUILD_VERSION
ENV BUILD_VERSION="$BUILD_VERSION"

USER root

ARG UID=1000
ARG GID=1000
ARG USERNAME=app
RUN <<EOF
    # Modify the existing `app` user from the base image to match host UID/GID
    usermod -u $UID $USERNAME
    groupmod -g $GID $USERNAME
    chown -R $UID:$GID /app /home/app
EOF

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
