FROM node:latest

WORKDIR /app-static
COPY code/package.json ./
COPY code/package-lock.json ./
COPY ./code ./
RUN npm install
RUN npm run build
#RUN npm ci --omit=dev
COPY ./code/public/static ./public/static


