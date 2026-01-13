# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Install envsubst for template rendering
RUN apk add --no-cache gettext

# Allow overriding the backend target at build time
ARG API_PROXY_TARGET="http://web:80"
ENV API_PROXY_TARGET=${API_PROXY_TARGET}

# Render nginx config from template with the provided backend target
COPY nginx.conf.template /etc/nginx/nginx.conf.template
RUN envsubst '${API_PROXY_TARGET}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf \
    && rm /etc/nginx/nginx.conf.template

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
