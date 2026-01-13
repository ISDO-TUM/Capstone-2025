# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Accept build argument for test mode
ARG VITE_TEST_MODE=false
ENV VITE_TEST_MODE=${VITE_TEST_MODE}

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Accept build arguments
ARG VITE_TEST_MODE=false
ARG DEPLOYMENT_ENV=local

# Copy nginx config files
COPY nginx.local.conf /etc/nginx/nginx.local.conf
COPY nginx.prod.conf /etc/nginx/nginx.prod.conf

# We select the appropriate config file based on deployment environment
# - DEPLOYMENT_ENV=local: Use nginx.local.conf (proxies to capstone_web:80)
# - DEPLOYMENT_ENV=production: Use nginx.prod.conf (proxies to Dokeploy backend)
RUN if [ "$DEPLOYMENT_ENV" = "production" ]; then \
      echo "Using production nginx config (Dokeploy)"; \
      cp /etc/nginx/nginx.prod.conf /etc/nginx/conf.d/default.conf; \
    else \
      echo "Using local nginx config (docker-compose)"; \
      cp /etc/nginx/nginx.local.conf /etc/nginx/conf.d/default.conf; \
    fi

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
