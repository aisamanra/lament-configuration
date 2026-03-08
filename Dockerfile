FROM node:25-slim AS base
RUN npm install -g pnpm@latest-10
WORKDIR /opt
COPY package.json pnpm-lock.yaml webpack.config.js .
COPY js/* js/.
RUN pnpm install
RUN pnpm webpack

FROM ghcr.io/astral-sh/uv:debian-slim
RUN mkdir -p /opt/run
WORKDIR /opt
RUN useradd -ms /bin/bash http && usermod -d /opt http
COPY static/* static/.
COPY --from=base /opt/static/lc.js static/lc.js
COPY js/serviceWorker.js js/.
COPY lc/*.py lc/.
COPY templates/*.mustache templates/.
COPY lament-configuration.py pyproject.toml uv.lock .
ENV LC_APP_PATH=http://remember.when.computer
ENV LC_DB_PATH=/opt/run/prod.db
RUN chown -R http:http .
USER http
RUN uv build && uv sync
CMD uv run --no-cache gunicorn --workers=2 --bind $SOCKET -m 007 lament-configuration:app
