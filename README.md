# pyDraw

A web-based UI for generating beautiful diagrams using the [diagrams](https://github.com/mingrammer/diagrams) library. This project provides a user-friendly interface for creating and visualizing diagrams without needing to write code directly.

## Features

- 🎨 Interactive code editor with syntax highlighting
- 📊 Real-time diagram preview
- 🔒 Security features including:
  - Input validation
  - Rate limiting
  - Secure error handling
  - Automatic cleanup of generated files
- 📝 Documentation and examples
- 💾 Download generated diagrams
- 🐳 Docker support for easy deployment

## Prerequisites

- Python 3.8 or higher
- Graphviz (required by the diagrams library)
- pip or Poetry for package management
- Docker and Docker Compose (for containerized deployment)

### Installing Graphviz

#### macOS
```bash
brew install graphviz
```

#### Ubuntu/Debian
```bash
sudo apt-get install graphviz
```

#### Windows
Download and install from [Graphviz website](https://graphviz.org/download/)

## Installation

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pydraw.git
cd pydraw
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Docker Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pydraw.git
cd pydraw
```

2. Create a `.env` file with your secret key:
```bash
echo "FLASK_SECRET_KEY=your-secret-key-here" > .env
```

3. Build and start the container:
```bash
docker-compose up -d
```

## Configuration

1. Create a `.env` file in the project root:
```bash
FLASK_SECRET_KEY=your-secret-key-here
```

2. (Optional) Configure additional settings in `config.py`:
- `TMP_DIR`: Directory for storing generated diagrams
- `RATE_LIMIT`: API rate limiting settings
- `MAX_CONTENT_LENGTH`: Maximum code size

## Running the Application

### Local Development

1. Start the Flask development server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5001
```

### Docker Deployment

#### Production Deployment

1. Start the application:
```bash
docker-compose up -d
```

2. View logs:
```bash
docker-compose logs -f
```

3. Stop the application:
```bash
docker-compose down
```

4. Rebuild and restart (after code changes):
```bash
docker-compose up -d --build
```

The application will be available at `http://localhost:5001`

#### Development Deployment with Monitoring

The development setup includes:
- Hot-reloading for code changes
- Prometheus for metrics collection
- Grafana for metrics visualization
- Loki for log aggregation
- Promtail for log collection

1. Start the development environment:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

2. Access the services:
- Application: http://localhost:5001
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

3. View logs:
```bash
docker-compose -f docker-compose.dev.yml logs -f
```

4. Stop the development environment:
```bash
docker-compose -f docker-compose.dev.yml down
```

5. Rebuild and restart:
```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

The development environment includes:
- Real-time code reloading
- Detailed metrics and monitoring
- Centralized logging
- Development-specific configurations

## Security Testing

The project includes a security test suite to verify protection against various attacks:

```bash
python test_security.py
```

This will:
- Test for common vulnerabilities
- Generate a detailed security report
- Provide recommendations for any issues found

## Project Structure

```
pydraw/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── static/            # Static files (CSS, JS)
├── templates/         # HTML templates
├── logs/             # Application logs
├── docker/           # Docker configuration
│   ├── Dockerfile    # Production Dockerfile
│   └── dev/         # Development Docker configuration
├── docker-compose.yml # Docker Compose configuration
└── tests/            # Test files
    ├── test_security.py
    └── test_cleanup.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Security

- All user input is validated
- Rate limiting is enabled by default
- Error messages are sanitized
- Generated files are automatically cleaned up
- Security headers are implemented

## License

This software is proprietary and confidential
Copyright (c) 2025 NāOM Lab LLC, Matthew Cascio (matt@naomlab.com)

This software is a larger work of [diagrams](https://github.com/mingrammer/diagrams) library, which is licensed under the MIT License.

## Acknowledgments

- [diagrams](https://github.com/mingrammer/diagrams) library
- [Flask](https://flask.palletsprojects.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Ace Editor](https://ace.c9.io/)

## Azure Deployment and Updates

### Initial Deployment

1. Log in to Azure:
```bash
az login
```

2. Create a resource group and container registry:
```bash
az group create --name pydraw-rg --location eastus
az acr create --resource-group pydraw-rg --name pydrawregistry --sku Basic
```

3. Enable admin access to the registry:
```bash
az acr update -n pydrawregistry --admin-enabled true
```

4. Log in to the container registry:
```bash
az acr credential show --name pydrawregistry
docker login pydrawregistry.azurecr.io --username <username> --password <password>
```

5. Build and push the Docker image:
```bash
docker build --platform linux/amd64 -t pydrawregistry.azurecr.io/pydraw:latest -f docker/Dockerfile .
docker push pydrawregistry.azurecr.io/pydraw:latest
```

6. Create and configure the web app:
```bash
az appservice plan create --name pydraw-plan --resource-group pydraw-rg --sku B1 --is-linux
az webapp create --resource-group pydraw-rg --plan pydraw-plan --name pydraw-app --deployment-container-image-name pydrawregistry.azurecr.io/pydraw:latest
```

### Making Updates

To update the application after making changes:

1. Make your code changes locally

2. Build a new Docker image with a version tag:
```bash
docker build --platform linux/amd64 -t pydrawregistry.azurecr.io/pydraw:v1.0.1 -f docker/Dockerfile .
```

3. Push the new image to Azure Container Registry:
```bash
docker push pydrawregistry.azurecr.io/pydraw:v1.0.1
```

4. Update the web app to use the new image:
```bash
az webapp config container set --name pydraw-app --resource-group pydraw-rg --docker-custom-image-name pydrawregistry.azurecr.io/pydraw:v1.0.1
```

5. Restart the web app to apply changes:
```bash
az webapp restart --name pydraw-app --resource-group pydraw-rg
```

### Monitoring and Logs

To view application logs:
```bash
az webapp log tail --name pydraw-app --resource-group pydraw-rg
```

To download logs for analysis:
```bash
az webapp log download --name pydraw-app --resource-group pydraw-rg
```
