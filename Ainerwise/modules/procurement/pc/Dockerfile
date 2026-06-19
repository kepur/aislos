FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.output ./output

ENV HOST=0.0.0.0
ENV PORT=3001

EXPOSE 3001
CMD ["node", "output/server/index.mjs"]
