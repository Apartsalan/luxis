FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Backend URL for Next.js rewrite proxy (server-side only, used at build time in next.config.ts)
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL

# Build
RUN npm run build

# SEC-25: Run as non-root user
RUN adduser -D -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Start
CMD ["npm", "start"]
