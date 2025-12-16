FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY web-app/package*.json ./

# Install dependencies
RUN npm install

# Copy application files
COPY web-app/ .

EXPOSE 3000

CMD ["npm", "start"]
