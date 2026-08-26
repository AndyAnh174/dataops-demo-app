# syntax=docker/dockerfile:1.7
FROM node:24.15.0-alpine3.23 AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM dependencies AS test
COPY . .
RUN npm test

FROM dependencies AS builder
COPY . .
RUN npm run build

FROM node:24.15.0-alpine3.23 AS runtime-base
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app
RUN rm -rf /usr/local/lib/node_modules/npm \
    && rm -f /usr/local/bin/npm /usr/local/bin/npx \
    && addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --ingroup app app

USER 10001:10001
EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]

FROM runtime-base AS prebuilt-runtime
COPY --chown=10001:10001 .next/standalone ./
COPY --chown=10001:10001 .next/static ./.next/static

FROM runtime-base AS runtime
COPY --from=builder --chown=10001:10001 /app/.next/standalone ./
COPY --from=builder --chown=10001:10001 /app/.next/static ./.next/static
