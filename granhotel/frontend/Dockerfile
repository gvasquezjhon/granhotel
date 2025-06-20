# ---- Stage 1: Build ----
# Use an official Node.js LTS image as a builder.
# Specify a version that is compatible with your project's dependencies (e.g., Vite, TypeScript).
FROM node:18-alpine AS builder

# Set the working directory in the container.
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock or pnpm-lock.yaml)
# This step leverages Docker's cache. These files are copied first, so `npm install`
# only re-runs if these files change.
COPY package.json package-lock.json* ./
# If using yarn:
# COPY package.json yarn.lock ./
# If using pnpm:
# COPY package.json pnpm-lock.yaml ./

# Install project dependencies.
# Using --frozen-lockfile (or equivalent for yarn/pnpm) is recommended for reproducible builds.
RUN npm install --frozen-lockfile
# If using yarn:
# RUN yarn install --frozen-lockfile
# If using pnpm:
# RUN pnpm install --frozen-lockfile

# Copy the rest of the application code into the container.
COPY . .

# Set the VITE_API_BASE_URL build argument (can be overridden at build time)
# This allows configuring the API endpoint during Docker image build.
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build the React application for production.
# This command typically runs `tsc && vite build` as per package.json.
RUN npm run build

# ---- Stage 2: Production ----
# Use a lightweight Nginx image to serve the static files.
FROM nginx:1.25-alpine

# Remove default Nginx public folder content
RUN rm -rf /usr/share/nginx/html/*

# Copy the build output (static files) from the "builder" stage to Nginx's web root.
COPY --from=builder /app/dist /usr/share/nginx/html

# Optional: Copy a custom Nginx configuration file if needed.
# For a typical SPA, you might need to configure Nginx to redirect all
# non-file requests to index.html to support client-side routing.
# Create nginx.conf in frontend directory for this.
COPY nginx.conf /etc/nginx/conf.d/default.conf
# If nginx.conf is not provided, Nginx will use its default config,
# which might not work well with SPAs (leading to 404s on deep links/refresh).

# Expose port 80 (default Nginx port).
EXPOSE 80

# Command to run Nginx in the foreground.
CMD ["nginx", "-g", "daemon off;"]
