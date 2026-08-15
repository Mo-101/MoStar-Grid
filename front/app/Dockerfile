# MoStar Grid Frontend — production build + serve
FROM node:20-slim AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --include=dev

COPY . .

ARG VITE_GRID_API_BASE
ARG VITE_MOSTAR_VOICE_URL
ARG VITE_ENABLE_LIVE_GRID_SERVICES=true
ENV VITE_GRID_API_BASE=${VITE_GRID_API_BASE}
ENV VITE_MOSTAR_VOICE_URL=${VITE_MOSTAR_VOICE_URL}
ENV VITE_ENABLE_LIVE_GRID_SERVICES=${VITE_ENABLE_LIVE_GRID_SERVICES}
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/serve.mjs ./serve.mjs
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/node_modules ./node_modules

ENV NODE_ENV=production
EXPOSE 41012
CMD ["node", "serve.mjs"]
