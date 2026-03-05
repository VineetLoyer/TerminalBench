FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ENV API_URL=http://api:8741
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
