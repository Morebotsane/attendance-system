FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --legacy-peer-deps
COPY . .
ARG VITE_KIOSK_PIN
ENV VITE_KIOSK_PIN=$VITE_KIOSK_PIN
ENV VITE_API_URL=/api/v1
RUN npm run build --legacy-peer-deps

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
