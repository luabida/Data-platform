# [Django Core]
ENV={{ENV}}
SECRET_KEY="{{SECRET_KEY}}"
ALLOWED_HOSTS="{{ALLOWED_HOSTS}}"
DJANGO_SETTINGS_MODULE={{DJANGO_SETTINGS_MODULE}}
NODE_ENV={{NODE_ENV}}

# [Django Image]
HOST_UID={{HOST_UID}}
HOST_GID={{HOST_GID}}
DJANGO_PORT={{DJANGO_PORT}}
DJANGO_HOST_DATA_PATH={{DJANGO_HOST_DATA_PATH}}
DJANGO_CONTAINER_DATA_PATH={{DJANGO_CONTAINER_DATA_PATH}}

# [Django Worker]
WORKER_PORT={{WORKER_PORT}}

# [Django OAuth]
SITE_DOMAIN={{SITE_DOMAIN}}
SITE_NAME={{SITE_NAME}}
GITHUB_CLIENT_ID={{GITHUB_CLIENT_ID}}
GITHUB_SECRET={{GITHUB_SECRET}}

# [Django PostgreSQL]
POSTGRES_HOST={{POSTGRES_HOST}}
POSTGRES_PORT={{POSTGRES_PORT}}
POSTGRES_USER={{POSTGRES_USER}}
POSTGRES_PASSWORD={{POSTGRES_PASSWORD}}
POSTGRES_DB={{POSTGRES_DB}}
DEFAULT_POSTGRES_URI={{DEFAULT_POSTGRES_URI}}
INFODENGUE_POSTGRES_URI={{INFODENGUE_POSTGRES_URI}}

# [Postgres Image]
POSTGRES_HOST_UID={{POSTGRES_HOST_UID}}
POSTGRES_HOST_GID={{POSTGRES_HOST_GID}}
POSTGRES_DATA_DIR_HOST={{POSTGRES_DATA_DIR_HOST}}
POSTGRES_CONF_DIR_HOST={{POSTGRES_CONF_DIR_HOST}}

# [Django Email]
DEFAULT_FROM_EMAIL={{DEFAULT_FROM_EMAIL}}
EMAIL_BACKEND={{EMAIL_BACKEND}}
EMAIL_HOST={{EMAIL_HOST}}
EMAIL_PORT={{EMAIL_PORT}}
EMAIL_HOST_USER={{EMAIL_HOST_USER}}
EMAIL_HOST_PASSWORD={{EMAIL_HOST_PASSWORD}}
EMAIL_USE_TLS={{EMAIL_USE_TLS}}

# [Mkdocs]
MKDOCS_PORT={{MKDOCS_PORT}}

# [Redis]
REDIS_PORT={{REDIS_PORT}}

# [EpiScanner]
EPISCANNER_HOST_DATA_DIR={{EPISCANNER_HOST_DATA_DIR}}

# [Mosqlient]
MOSQLIENT_API_URL={{MOSQLIENT_API_URL}}
