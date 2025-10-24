FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY app ./app
COPY components ./components
COPY lib ./lib
COPY public ./public
COPY next.config.js tsconfig.json tailwind.config.js postcss.config.js .

EXPOSE 3456

CMD ["npm", "run", "dev", "--", "--port", "3456"]
