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
# Copy only api source, shared packages and root scripts (build uses scripts/prisma-generate-safe.mjs)
COPY apps/api apps/api
COPY packages packages
COPY scripts scripts
RUN npm run build -w apps/api

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S progresia && adduser -S progresia -G progresia
ENV NODE_PATH=/app/apps/api/node_modules:/app/node_modules
COPY --from=build /app/node_modules node_modules
COPY --from=build /app/apps/api/node_modules apps/api/node_modules
COPY --from=build /app/apps/api/dist dist
COPY --from=build /app/apps/api/prisma prisma
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -qO- http://localhost:3000/api/health || exit 1
USER progresia
CMD ["sh", "-c", "node apps/api/node_modules/prisma/build/index.js migrate deploy --schema ./prisma/schema.prisma && node dist/main.js"]
