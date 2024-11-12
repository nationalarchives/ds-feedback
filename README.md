# TNA Python Flask Application

## Quickstart

```sh
# Build and start the container
docker compose up -d
```

### Add the static assets

During the first time install, your `app/static/assets` directory will be empty.

As you mount the project directory to the `/app` volume, the static assets from TNA Frontend installed inside the container will be "overwritten" by your empty directory.

To add back in the static assets, run:

```sh
docker compose exec app cp -r /app/node_modules/@nationalarchives/frontend/nationalarchives/assets /app/app/static
```

### Run tests

```sh
docker compose exec dev poetry run python /app/manage.py test
```

### Format and lint code

```sh
docker compose exec dev format
```

## Environment variables

In addition to the [base Docker image variables](https://github.com/nationalarchives/docker/blob/main/docker/tna-python-django/README.md#environment-variables), this application has support for:

| Variable                 | Purpose                                                   | Default                                                   |
| ------------------------ | --------------------------------------------------------- | --------------------------------------------------------- |
| `DJANGO_SETTINGS_MODULE` | The configuration to use                                  | `config.settings.production`                              |
| `ALLOWED_HOSTS`          | A comma-separated list of allowed hosts                   | _none_ on production and staging, `*` on develop and test |
| `USE_X_FORWARDED_HOST`   | Use the `X-Forwarded-Host` header in preference to `Host` | `False`                                                   |
| `DEBUG`                  | If true, allow debugging                                  | `False`                                                   |
| `COOKIE_DOMAIN`          | The domain to save cookie preferences against             | _none_                                                    |
| `DATABASE_NAME`          | The name of the Postgres database                         | _none_                                                    |
| `DATABASE_USER`          | The username needed to access the Postgres database       | _none_                                                    |
| `DATABASE_PASSWORD`      | The password needed to access the Postgres database       | _none_                                                    |
| `DATABASE_HOST`          | The Postgres database host                                | _none_                                                    |
| `DATABASE_PORT`          | The Postgres database port                                | `5432`                                                    |
| `CSP_IMG_SRC`            | A comma separated list of CSP rules for `img-src`         | `'self'`                                                  |
| `CSP_SCRIPT_SRC`         | A comma separated list of CSP rules for `script-src`      | `'self'`                                                  |
| `CSP_SCRIPT_SRC_ELEM`    | A comma separated list of CSP rules for `script-src-elem` | `'self'`                                                  |
| `CSP_STYLE_SRC`          | A comma separated list of CSP rules for `style-src`       | `'self'`                                                  |
| `CSP_STYLE_SRC_ELEM`     | A comma separated list of CSP rules for `style-src-elem`  | `'self'`                                                  |
| `CSP_FONT_SRC`           | A comma separated list of CSP rules for `font-src`        | `'self'`                                                  |
| `CSP_CONNECT_SRC`        | A comma separated list of CSP rules for `connect-src`     | `'self'`                                                  |
| `CSP_MEDIA_SRC`          | A comma separated list of CSP rules for `media-src`       | `'self'`                                                  |
| `CSP_WORKER_SRC`         | A comma separated list of CSP rules for `worker-src`      | `'self'`                                                  |
| `CSP_FRAME_SRC`          | A comma separated list of CSP rules for `frame-src`       | `'self'`                                                  |
| `GA4_ID`                 | The Google Analytics 4 ID                                 | _none_                                                    |
