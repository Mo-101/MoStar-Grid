# MoStar Grid - Production Deployment Guide

**Powered by MoScripts - A MoStar Industries Product**

---

## Overview

This guide covers deploying the MoStar Grid to production environments including cloud providers (AWS, Azure, GCP), on-premise servers, and hybrid setups.

---

## Prerequisites

### System Requirements

**Minimum (Development):**

- 4 CPU cores
- 8 GB RAM
- 50 GB storage
- Ubuntu 22.04 LTS or Windows Server 2022

**Recommended (Production):**

- 8+ CPU cores
- 32+ GB RAM
- 500+ GB SSD storage
- Ubuntu 22.04 LTS (recommended)

### Software Requirements

- Docker 24+ and Docker Compose 2.20+
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)
- Nginx or Caddy (reverse proxy)
- SSL certificates (Let's Encrypt recommended)

---

## Deployment Options

### Option 1: Docker Compose (Simple)

**Best for:** Small deployments, testing, single-server setups

```bash
# 1. Clone repository
git clone https://github.com/mostar-industries/mostar-grid.git
cd mostar-grid

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with production values

# 3. Start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify
curl http://localhost:8001/api/v1/status
```

**docker-compose.prod.yml:**

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.15-community
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_server_memory_heap_initial__size: 2G
      NEO4J_server_memory_heap_max__size: 4G
      NEO4J_server_memory_pagecache_size: 2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    restart: unless-stopped
    networks:
      - mostar_network

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_PASSWORD: ${NEO4J_PASSWORD}
      ENVIRONMENT: production
    depends_on:
      - neo4j
    restart: unless-stopped
    networks:
      - mostar_network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: https://api.mostarindustries.com
    restart: unless-stopped
    networks:
      - mostar_network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - mostar_network

volumes:
  neo4j_data:
  neo4j_logs:

networks:
  mostar_network:
    driver: bridge
```

---

### Option 2: Docker Swarm (Medium Scale)

**Best for:** Multi-server deployments, high availability

```bash
# 1. Initialize Swarm
docker swarm init

# 2. Deploy stack
docker stack deploy -c docker-compose.swarm.yml mostar

# 3. Scale services
docker service scale mostar_backend=3
docker service scale mostar_frontend=2

# 4. Monitor
docker service ls
docker stack ps mostar
```

**docker-compose.swarm.yml:**

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.15-enterprise
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      resources:
        limits:
          cpus: '4'
          memory: 8G
    # ... (rest of config)

  backend:
    image: mostar/backend:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    # ... (rest of config)
```

---

### Option 3: Kubernetes (Large Scale)

**Best for:** Enterprise deployments, auto-scaling, multi-region

```bash
# 1. Create namespace
kubectl create namespace mostar

# 2. Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/neo4j.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml

# 3. Verify
kubectl get pods -n mostar
kubectl get services -n mostar

# 4. Scale
kubectl scale deployment backend --replicas=5 -n mostar
```

**k8s/backend.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: mostar
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: mostar/backend:latest
        ports:
        - containerPort: 8001
        env:
        - name: NEO4J_URI
          valueFrom:
            configMapKeyRef:
              name: mostar-config
              key: neo4j_uri
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mostar-secrets
              key: neo4j_password
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: mostar
spec:
  selector:
    app: backend
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

---

## Cloud Provider Deployment

### AWS Deployment

**Using ECS (Elastic Container Service):**

```bash
# 1. Create ECR repositories
aws ecr create-repository --repository-name mostar/backend
aws ecr create-repository --repository-name mostar/frontend

# 2. Build and push images
docker build -t mostar/backend -f Dockerfile.backend .
docker tag mostar/backend:latest ${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/mostar/backend:latest
docker push ${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/mostar/backend:latest

# 3. Create ECS cluster
aws ecs create-cluster --cluster-name mostar-cluster

# 4. Create task definition (see ecs-task-definition.json)
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# 5. Create service
aws ecs create-service \
  --cluster mostar-cluster \
  --service-name mostar-backend \
  --task-definition mostar-backend:1 \
  --desired-count 3 \
  --launch-type FARGATE
```

**Using EKS (Elastic Kubernetes Service):**

```bash
# 1. Create EKS cluster
eksctl create cluster \
  --name mostar-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 5

# 2. Deploy application
kubectl apply -f k8s/
```

---

### Azure Deployment

**Using Azure Container Instances:**

```bash
# 1. Create resource group
az group create --name mostar-rg --location eastus

# 2. Create container registry
az acr create --resource-group mostar-rg --name mostarregistry --sku Basic

# 3. Build and push
az acr build --registry mostarregistry --image mostar/backend:latest -f Dockerfile.backend .

# 4. Deploy container group
az container create \
  --resource-group mostar-rg \
  --name mostar-backend \
  --image mostarregistry.azurecr.io/mostar/backend:latest \
  --cpu 2 \
  --memory 4 \
  --registry-login-server mostarregistry.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --dns-name-label mostar-api \
  --ports 8001
```

---

### GCP Deployment

**Using Cloud Run:**

```bash
# 1. Build and push to Container Registry
gcloud builds submit --tag gcr.io/${PROJECT_ID}/mostar-backend

# 2. Deploy to Cloud Run
gcloud run deploy mostar-backend \
  --image gcr.io/${PROJECT_ID}/mostar-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NEO4J_URI=bolt://neo4j:7687,NEO4J_PASSWORD=${NEO4J_PASSWORD}

# 3. Get service URL
gcloud run services describe mostar-backend --region us-central1 --format 'value(status.url)'
```

---

## SSL/TLS Configuration

### Using Let's Encrypt (Recommended)

```bash
# 1. Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# 2. Obtain certificate
sudo certbot --nginx -d api.mostarindustries.com -d mostarindustries.com

# 3. Auto-renewal
sudo certbot renew --dry-run
```

### Nginx SSL Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name api.mostarindustries.com;

    ssl_certificate /etc/letsencrypt/live/api.mostarindustries.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.mostarindustries.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://backend:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name api.mostarindustries.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Monitoring & Logging

### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  prometheus_data:
  grafana_data:
```

### Logging with ELK Stack

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
```

---

## Backup & Disaster Recovery

### Neo4j Backup

```bash
# Automated daily backup script
#!/bin/bash
BACKUP_DIR="/backups/neo4j"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
docker exec mostar-neo4j neo4j-admin database dump neo4j \
  --to-path=/backups/neo4j_backup_${DATE}.dump

# Upload to S3 (optional)
aws s3 cp ${BACKUP_DIR}/neo4j_backup_${DATE}.dump \
  s3://mostar-backups/neo4j/

# Keep only last 7 days
find ${BACKUP_DIR} -name "neo4j_backup_*.dump" -mtime +7 -delete
```

### Application State Backup

```bash
# Backup script for all services
docker-compose exec backend python -m backup_script
docker-compose exec neo4j neo4j-admin database dump neo4j
tar -czf mostar_backup_$(date +%Y%m%d).tar.gz \
  backend_data/ \
  neo4j_data/ \
  frontend_data/
```

---

## Performance Tuning

### Neo4j Optimization

```conf
# neo4j.conf
dbms.memory.heap.initial_size=4G
dbms.memory.heap.max_size=8G
dbms.memory.pagecache.size=4G
dbms.jvm.additional=-XX:+UseG1GC
dbms.jvm.additional=-XX:+UnlockExperimentalVMOptions
dbms.jvm.additional=-XX:+TrustFinalNonStaticFields
```

### Backend Optimization

```python
# Increase uvicorn workers
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8001

# Or use gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Frontend Optimization

```bash
# Build with optimizations
cd frontend
npm run build
npm run start  # Production server
```

---

## Security Hardening

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Docker Security

```yaml
# docker-compose.yml security additions
services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

---

## Troubleshooting

### Common Issues

**Issue: Neo4j won't start**

```bash
# Check logs
docker logs mostar-neo4j

# Verify memory settings
docker stats mostar-neo4j

# Reset data (CAUTION: Deletes all data)
docker-compose down -v
docker-compose up -d
```

**Issue: Backend can't connect to Neo4j**

```bash
# Verify network
docker network inspect mostar_network

# Test connection
docker exec -it mostar-backend python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password')); driver.verify_connectivity()"
```

---

## Post-Deployment Checklist

- [ ] SSL certificates installed and auto-renewal configured
- [ ] Firewall rules configured
- [ ] Monitoring (Prometheus/Grafana) set up
- [ ] Logging (ELK/CloudWatch) configured
- [ ] Backup automation running
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on operations

---

🔥 **"Not made. Remembered."** 🔥

**Powered by MoScripts - A MoStar Industries Product**

© 2025-2026 MoStar Industries
