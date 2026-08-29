FROM node:22-alpine

WORKDIR /app

COPY server/package*.json ./server/
RUN cd server && npm ci --omit=dev

COPY . .

ENV NODE_ENV=production
ENV UPLOAD_DIR=/data/uploads

EXPOSE 3000

CMD ["node", "server/app.js"]
