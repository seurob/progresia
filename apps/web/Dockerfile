FROM node:22-alpine AS build
WORKDIR /app
# Copy all workspace package.json files for npm ci to resolve the monorepo graph
COPY package*.json ./
COPY apps/api/package*.json apps/api/
COPY apps/web/package*.json apps/web/
COPY packages/config/package*.json packages/config/
COPY packages/contracts/package*.json packages/contracts/
COPY packages/shared/package*.json packages/shared/
RUN npm ci
COPY apps/web apps/web
COPY packages packages
RUN npm run build -w apps/web

FROM nginx:1.27-alpine
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost/ || exit 1
