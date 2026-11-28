# A small React app laid out the way a cache-friendly Dockerfile should be: system packages, then
# dependencies from the lockfile, then the source. Editing src/ only rebuilds the last two steps.

FROM node:24-alpine@sha256:116b800c3754b440ee0aa3ed2f20f5bf3d99a554bfd9adeea09ea8017f6e85f5 AS base
RUN apk add --no-cache git
WORKDIR /app

FROM base AS deps
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM deps AS build
COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src
RUN npm run build

FROM nginx:stable-alpine@sha256:8eb04fe3b385090e9aa02961f77398ad09b6bf33ab07f6669a5bb7acce22c0d3
COPY --from=build /app/dist /usr/share/nginx/html
