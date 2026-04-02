# Dashboard - React Frontend
# Multi-stage build | Node 20-alpine

# -- Stage 1: Build ----------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /build

# Copy dependencies first for better dockerd caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest of the app and build
COPY . .
RUN npm run build

# -- Stage 2: Runtime (Nginx) ----------------------------------------------------
FROM nginx:alpine

LABEL maintainer="dashboard"
LABEL description="Dashboard - React Frontend"

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built frontend assets from the builder stage
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy our custom nginx API proxy config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 3001
EXPOSE 3001

CMD ["nginx", "-g", "daemon off;"]
