# Multi-stage build for React frontend
# Stage 1: Build
FROM node:22-alpine AS build

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Production with nginx
FROM nginx:alpine

# Accept backend host as build argument
ARG BACKEND_HOST=backend
ENV BACKEND_HOST=${BACKEND_HOST}

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Expose port
EXPOSE 80

# nginx will automatically process templates in /etc/nginx/templates/
# and substitute environment variables
CMD ["nginx", "-g", "daemon off;"]
