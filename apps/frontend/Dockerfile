# syntax=docker/dockerfile:1

# Stage 1: Dependencies
FROM node:22-slim AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
# Install pnpm and dependencies
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Stage 2: Builder
FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Install pnpm in builder stage too for the build script
RUN npm install -g pnpm

# Run build (this will run 'next build' and then 'webpack' via pnpm)
RUN pnpm build

# Stage 3: Runner
FROM node:22-slim AS runner
WORKDIR /app

ENV NODE_ENV=production

# Create a non-privileged user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Use npm start to run the Next.js app
CMD ["npm", "start"]
