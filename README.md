# DS Feedback Service

This project is An API and administrative tool for collecting quick user feedback across TNA sites, in the style of the [GOV.UK feedback component](https://insidegovuk.blog.gov.uk/2022/03/28/making-the-gov-uk-feedback-component-more-accessible/#:~:text=What%20is%20the%20feedback%20component,also%20can%20demonstrate%20any%20concerns.).

See [Key Concepts](/docs/key-concepts.md) for further information.

This project uses the Django admin interface to manage feedback prompt questions and multiple choice answers, and decide which prompts are offered to users on which URLs. This is intended to be a temporary interface which will be replaced with a custom UI.

See [Technical Guide](/docs/technical-guide.md) for more technical information.

## Installation & Usage

Use docker compose to run the server:

```sh
# Build and start the container
docker compose up -d
```

For development, you will need to create a superuser account:

```sh
docker compose exec app poetry run python /app/manage.py createsuperuser
```

Then access the server at [http://localhost:65527/](http://localhost:65527/) and login.

### Other resources:

- [Admin interface](http://localhost:65527/admin/)
- [Swagger API docs](http://localhost:65527/api/v1/schema/swagger/)
- [Postman collection](/docs/tna-feedback-api.postman_collection.json)

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
docker compose run dev ./format.sh
```

### Dependency management

Install dependencies through the app container:

```sh
docker compose exec app poetry add django
```

Then sync your local dependencies, if desired:

```sh
poetry install
```

### Migration management:

Manage migrations through the app container:

```sh
docker compose exec app poetry run python /app/manage.py makemigrations
docker compose exec app poetry run python /app/manage.py migrate
```

## Environment variables

In addition to the [base Docker image variables](https://github.com/nationalarchives/docker/blob/main/docker/tna-python-django/README.md#environment-variables), this application has support for:

| Variable                 | Purpose                                                        | Default                                                   |
| ------------------------ | -------------------------------------------------------------- | --------------------------------------------------------- |
| `DJANGO_SETTINGS_MODULE` | The configuration to use                                       | `config.settings.production`                              |
| `ALLOWED_HOSTS`          | A comma-separated list of allowed hosts                        | _none_ on production and staging, `*` on develop and test |
| `USE_X_FORWARDED_HOST`   | Use the `X-Forwarded-Host` header in preference to `Host`      | `False`                                                   |
| `DEBUG`                  | If true, allow debugging                                       | `False`                                                   |
| `COOKIE_DOMAIN`          | The domain to save cookie preferences against                  | _none_                                                    |
| `DATABASE_URL`           | The database's URL (`postgres://USER:PASSWORD@HOST:PORT/NAME`) | _none_                                                    |
| `CSP_IMG_SRC`            | A comma separated list of CSP rules for `img-src`              | `'self'`                                                  |
| `CSP_SCRIPT_SRC`         | A comma separated list of CSP rules for `script-src`           | `'self'`                                                  |
| `CSP_SCRIPT_SRC_ELEM`    | A comma separated list of CSP rules for `script-src-elem`      | `'self'`                                                  |
| `CSP_STYLE_SRC`          | A comma separated list of CSP rules for `style-src`            | `'self'`                                                  |
| `CSP_STYLE_SRC_ELEM`     | A comma separated list of CSP rules for `style-src-elem`       | `'self'`                                                  |
| `CSP_FONT_SRC`           | A comma separated list of CSP rules for `font-src`             | `'self'`                                                  |
| `CSP_CONNECT_SRC`        | A comma separated list of CSP rules for `connect-src`          | `'self'`                                                  |
| `CSP_MEDIA_SRC`          | A comma separated list of CSP rules for `media-src`            | `'self'`                                                  |
| `CSP_WORKER_SRC`         | A comma separated list of CSP rules for `worker-src`           | `'self'`                                                  |
| `CSP_FRAME_SRC`          | A comma separated list of CSP rules for `frame-src`            | `'self'`                                                  |
| `GA4_ID`                 | The Google Analytics 4 ID                                      | _none_                                                    |
