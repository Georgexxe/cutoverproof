FROM node:22-bookworm-slim AS web-build

WORKDIR /build/web
RUN corepack enable
COPY web/package.json web/pnpm-lock.yaml web/pnpm-workspace.yaml web/.npmrc ./
RUN pnpm install --frozen-lockfile
COPY web/ ./
RUN pnpm build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
RUN apt-get update \
    && apt-get install --yes --no-install-recommends postgresql postgresql-client \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 cutoverproof

COPY src/ ./src/
COPY scenarios/ ./scenarios/
COPY examples/ ./examples/
COPY artifacts/evaluation/ ./artifacts/evaluation/
COPY scripts/start-cloud-run.sh ./scripts/start-cloud-run.sh
COPY --from=web-build /build/web/dist/client ./web/dist/client/

RUN mkdir -p ./artifacts/imported_scenarios ./artifacts/runs ./artifacts/timelines ./artifacts/trajectories \
    && chmod +x ./scripts/start-cloud-run.sh \
    && chown -R cutoverproof:cutoverproof /app
USER cutoverproof

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8080') + '/api/health', timeout=4)" || exit 1
CMD ["./scripts/start-cloud-run.sh"]
