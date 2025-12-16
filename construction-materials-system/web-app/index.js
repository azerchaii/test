const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';

// Middleware
app.use(express.static('public'));
app.use(express.json());

// Routes
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Construction Materials System</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
          background-color: #f5f5f5;
        }
        h1 {
          color: #333;
          border-bottom: 3px solid #007bff;
          padding-bottom: 10px;
        }
        .container {
          background: white;
          padding: 30px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .info {
          background-color: #e7f3ff;
          border-left: 4px solid #007bff;
          padding: 15px;
          margin: 20px 0;
        }
        .links {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 15px;
          margin-top: 20px;
        }
        .link-card {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 20px;
          border-radius: 8px;
          text-decoration: none;
          transition: transform 0.2s;
        }
        .link-card:hover {
          transform: translateY(-5px);
        }
        .link-card h3 {
          margin: 0 0 10px 0;
        }
        .link-card p {
          margin: 0;
          opacity: 0.9;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>🏗️ Construction Materials System</h1>
        <div class="info">
          <strong>Welcome to the Construction Materials Management System</strong>
          <p>This system provides comprehensive material inventory management, procurement, and request handling for construction projects.</p>
        </div>
        
        <h2>System Components</h2>
        <div class="links">
          <a href="${API_BASE_URL.replace('/api/v1', '')}/docs" class="link-card">
            <h3>📚 API Documentation</h3>
            <p>Interactive API documentation with Swagger UI</p>
          </a>
          <a href="http://localhost:15672" class="link-card">
            <h3>🐰 RabbitMQ Management</h3>
            <p>Message queue monitoring and management</p>
          </a>
        </div>

        <h2>Available Services</h2>
        <ul>
          <li><strong>Inventory Service</strong> - Material inventory management (gRPC: 50051)</li>
          <li><strong>Procurement Service</strong> - Supplier and procurement management (gRPC: 50052)</li>
          <li><strong>Request Service</strong> - Material request handling (gRPC: 50053)</li>
          <li><strong>Notification Service</strong> - Email and notification dispatch (gRPC: 50054)</li>
          <li><strong>API Gateway</strong> - REST API entry point (HTTP: 8000)</li>
        </ul>

        <div class="info">
          <strong>API Base URL:</strong> ${API_BASE_URL}
        </div>
      </div>
    </body>
    </html>
  `);
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'web-app', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`Web app running on port ${PORT}`);
  console.log(`API Gateway: ${API_BASE_URL}`);
});
