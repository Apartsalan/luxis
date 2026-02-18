FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Accept API URL as build argument (NEXT_PUBLIC_ vars must be available at build time)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build
RUN npm run build

# Start
CMD ["npm", "start"]
