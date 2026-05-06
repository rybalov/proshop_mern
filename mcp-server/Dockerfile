FROM node:18-alpine

WORKDIR /app

COPY mcp-server/package.json mcp-server/package-lock.json ./
RUN npm ci

COPY mcp-server/src/ ./src/
COPY mcp-server/tsconfig.json ./

RUN npm run build

ENTRYPOINT ["node", "dist/index.js"]
