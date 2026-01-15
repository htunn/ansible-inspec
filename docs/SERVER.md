# InSpec Execution Server

Web UI and REST API for ansible-inspec compliance testing.

## Overview

The InSpec Execution Server provides a modern, web-based interface for managing and executing InSpec compliance profiles. It includes:

- **📊 Web UI (Streamlit)**: Interactive dashboard for job management
- **🔌 REST API (FastAPI)**: RESTful API for programmatic access
- **📚 Auto-generated API Docs**: Swagger UI and ReDoc documentation
- **🚀 Job Templates**: Reusable templates for compliance checks
- **📋 Job Execution**: Background job execution with status tracking
- **🔄 Workflow Management**: Multi-job workflow orchestration

## Features

### Job Templates

Create reusable templates for InSpec profile executions:

```json
{
  "name": "Linux Baseline Check",
  "description": "DevSec Linux Baseline compliance scan",
  "profile_path": "dev-sec/linux-baseline",
  "supermarket": true,
  "reporter": "cli json",
  "inventory": "/path/to/inventory.yml"
}
```

### Job Execution

Launch jobs from templates with custom parameters:

- Background execution
- Real-time status updates
- Output capture (stdout/stderr)
- JSON result summaries

### Workflow Templates

Chain multiple jobs together for complex compliance scenarios:

```json
{
  "name": "Full Security Audit",
  "nodes": [
    {
      "identifier": "baseline-check",
      "job_template_id": "..."
    },
    {
      "identifier": "remediation",
      "job_template_id": "...",
      "success_nodes": ["verify-fix"]
    }
  ]
}
```

## Quick Start

### Installation

Install ansible-inspec with server dependencies:

```bash
pip install ansible-inspec

# Or install from source with server extras
pip install -e ".[server]"
```

### Starting the Server

Start both Web UI and API server:

```bash
ansible-inspec start-server
```

This will start:
- **Web UI (Streamlit)** at http://localhost:8081
- **REST API (FastAPI)** at http://localhost:8080
- **API Docs (Swagger)** at http://localhost:8080/docs
- **API Docs (ReDoc)** at http://localhost:8080/redoc

### Custom Configuration

```bash
# Custom host and port
ansible-inspec start-server --host 0.0.0.0 --port 9000

# Custom data directory
ansible-inspec start-server --data-dir /var/lib/ansible-inspec

# API server only (no Web UI)
ansible-inspec start-server --no-ui
```

## Web UI Usage

### Dashboard

The dashboard provides an overview of:
- Total job templates
- Job execution statistics
- Success rate metrics
- Recent job history

### Creating Job Templates

1. Navigate to "Create Template" page
2. Fill in the template details:
   - **Name**: Descriptive name for the template
   - **Description**: Optional description
   - **Profile Path**: Path to InSpec profile or Supermarket name
   - **Inventory**: Ansible inventory file (optional)
   - **Target**: Direct target (ssh://, docker://, etc.)
   - **Reporter**: Output format (default: "cli json")
3. Click "Create Template"

### Launching Jobs

1. Go to "Job Templates" page
2. Find your template
3. Click "🚀 Launch" button
4. Monitor job progress in "Jobs" page

## REST API Usage

### Authentication

Currently, the API does not require authentication. For production use, implement authentication middleware.

### API Endpoints

#### Job Templates

**List all job templates**
```http
GET /api/v1/job_templates/
```

**Create a job template**
```http
POST /api/v1/job_templates/
Content-Type: application/json

{
  "name": "My Compliance Check",
  "profile_path": "dev-sec/linux-baseline",
  "supermarket": true,
  "reporter": "cli json"
}
```

**Get a specific template**
```http
GET /api/v1/job_templates/{template_id}/
```

**Update a template**
```http
PUT /api/v1/job_templates/{template_id}/
Content-Type: application/json

{
  "description": "Updated description"
}
```

**Delete a template**
```http
DELETE /api/v1/job_templates/{template_id}/
```

**Launch a job from template**
```http
POST /api/v1/job_templates/{template_id}/launch/
Content-Type: application/json

{
  "extra_vars": {}
}
```

#### Jobs

**List all jobs**
```http
GET /api/v1/jobs/
```

**Filter jobs by status**
```http
GET /api/v1/jobs/?status=successful
```

**Get a specific job**
```http
GET /api/v1/jobs/{job_id}/
```

**Get job output**
```http
GET /api/v1/jobs/{job_id}/stdout/
```

**Cancel a running job**
```http
POST /api/v1/jobs/{job_id}/cancel/
```

#### Statistics

**Get server statistics**
```http
GET /api/v1/statistics/
```

Returns:
```json
{
  "job_templates": 5,
  "total_jobs": 42,
  "successful_jobs": 38,
  "failed_jobs": 4,
  "running_jobs": 0,
  "success_rate": 90.5
}
```

### Python Client Example

```python
import requests

API_BASE = "http://localhost:8080/api/v1"

# Create a job template
template = {
    "name": "Linux Security Baseline",
    "description": "DevSec Linux Baseline checks",
    "profile_path": "dev-sec/linux-baseline",
    "supermarket": True,
    "reporter": "cli json"
}

response = requests.post(f"{API_BASE}/job_templates/", json=template)
template_id = response.json()["id"]

# Launch a job
launch_response = requests.post(
    f"{API_BASE}/job_templates/{template_id}/launch/",
    json={"extra_vars": {}}
)
job = launch_response.json()

print(f"Job {job['id']} launched with status: {job['status']}")

# Check job status
import time
while True:
    job_response = requests.get(f"{API_BASE}/jobs/{job['id']}/")
    job_data = job_response.json()
    
    if job_data['status'] in ['successful', 'failed', 'canceled']:
        print(f"Job finished with status: {job_data['status']}")
        break
    
    print(f"Job status: {job_data['status']}")
    time.sleep(5)

# Get job output
output_response = requests.get(f"{API_BASE}/jobs/{job['id']}/stdout/")
print(output_response.json()['stdout'])
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                  Streamlit Web UI                       │
│                  (Port 8081)                            │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP Requests
                     ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│              FastAPI REST API Server                    │
│                  (Port 8080)                            │
│                                                         │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐     │
│  │ API Routes │  │  Storage   │  │ Job Executor │     │
│  └────────────┘  └────────────┘  └──────────────┘     │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│              File-based Storage                         │
│                                                         │
│  ├── job_templates/                                     │
│  ├── jobs/                                              │
│  └── workflow_templates/                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│         ansible-inspec Core Engine                      │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐       │
│  │  Runner  │  │ InSpec   │  │ Ansible        │       │
│  │          │  │ Adapter  │  │ Integration    │       │
│  └──────────┘  └──────────┘  └────────────────┘       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Data Storage

The server uses file-based storage (JSON files) by default. Data is organized as:

```
data/
├── job_templates/
│   └── {template_id}.json
├── jobs/
│   ├── {job_id}.json
│   └── {job_id}/
│       ├── stdout.txt
│       ├── stderr.txt
│       └── report.json
└── workflow_templates/
    └── {workflow_id}.json
```

## Security Considerations

⚠️ **Important Security Notes**:

1. **No Authentication**: The default setup does not include authentication. For production use:
   - Add authentication middleware
   - Use HTTPS/TLS
   - Implement role-based access control (RBAC)

2. **Network Access**: Bind to `127.0.0.1` instead of `0.0.0.0` for local-only access

3. **Data Protection**: Ensure the data directory has proper file permissions

## Production Deployment

### Using systemd

Create `/etc/systemd/system/ansible-inspec-server.service`:

```ini
[Unit]
Description=InSpec Execution Server
After=network.target

[Service]
Type=simple
User=ansible-inspec
WorkingDirectory=/opt/ansible-inspec
ExecStart=/usr/local/bin/ansible-inspec start-server \
    --host 0.0.0.0 \
    --port 8080 \
    --data-dir /var/lib/ansible-inspec
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ansible-inspec-server
sudo systemctl start ansible-inspec-server
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . /app
RUN pip install -e .

EXPOSE 8080 8081

CMD ["ansible-inspec", "start-server", "--host", "0.0.0.0"]
```

Build and run:
```bash
docker build -t ansible-inspec-server .
docker run -p 8080:8080 -p 8081:8081 -v /data:/app/data ansible-inspec-server
```

## Troubleshooting

### Server won't start

**Check port availability:**
```bash
lsof -i :8080
lsof -i :8081
```

**Use different ports:**
```bash
ansible-inspec start-server --port 9000
```

### Jobs not executing

**Check ansible-inspec CLI works:**
```bash
ansible-inspec exec dev-sec/linux-baseline --supermarket
```

**Check job logs:**
```bash
cat data/jobs/{job-id}/stderr.txt
```

### API not accessible

**Verify server is running:**
```bash
curl http://localhost:8080/api/v1/
```

**Check firewall rules:**
```bash
sudo ufw status
```

## License

InSpec Execution Server is part of ansible-inspec and is licensed under GPL-3.0.

This implementation is designed to avoid trademark and licensing issues by:
- Using distinct naming ("InSpec Execution Server")
- Providing independent functionality
- Not claiming compatibility with proprietary platforms
- Maintaining full GPL-3.0 compliance

## Contributing

Contributions are welcome! Please see the main project's CONTRIBUTING.md for guidelines.

## Support

- **Documentation**: See main README and docs/
- **Issues**: https://github.com/Htunn/ansible-inspec/issues
- **Community**: Create a discussion for questions and ideas
