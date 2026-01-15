# Example Ansible Playbooks for InSpec Execution Server

This directory contains demo playbooks that demonstrate using the InSpec Execution Server to run Ansible playbooks with environment variables.

## Available Playbooks

### 1. demo_compliance.yml

A comprehensive compliance check playbook that demonstrates environment variable usage.

**Environment Variables:**
- `CHECK_SSH` - Enable/disable SSH checks (default: `true`)
- `CHECK_FIREWALL` - Enable/disable firewall checks (default: `true`)
- `MIN_DISK_SPACE_GB` - Minimum required disk space in GB (default: `10`)
- `REQUIRED_PACKAGES` - Comma-separated list of required packages (default: `vim,curl,wget`)

**Example Usage via UI:**

1. Navigate to "Create Template" in the Web UI
2. Fill in the form:
   - **Name**: Demo Compliance Check
   - **Description**: System compliance verification
   - **Profile Path / Playbook**: `examples/playbooks/demo_compliance.yml`
   - **Check**: "Use Ansible Playbook"
   - **Inventory**: Leave blank for localhost
3. In the **Environment Variables** section, add:
   ```
   CHECK_SSH=true
   MIN_DISK_SPACE_GB=20
   REQUIRED_PACKAGES=vim,curl,git,htop
   ```
4. Click "Create Template"
5. Go to "Job Templates" and click "🚀 Launch"

**What it checks:**
- Available disk space
- SSH service status
- Required packages installation
- System information summary

---

### 2. web_server_compliance.yml

Security compliance checks for web servers.

**Environment Variables:**
- `WEB_SERVER_TYPE` - Web server to check (default: `nginx`, options: `nginx`, `apache2`, `httpd`)
- `CHECK_SSL` - Enable SSL/TLS checks (default: `true`)
- `MIN_TLS_VERSION` - Minimum TLS version (default: `1.2`)
- `REQUIRED_HEADERS` - Comma-separated list of required security headers

**Example Usage via UI:**

1. Create a new template with:
   - **Name**: Web Server Security Audit
   - **Profile Path / Playbook**: `examples/playbooks/web_server_compliance.yml`
   - **Check**: "Use Ansible Playbook"
2. Environment Variables:
   ```
   WEB_SERVER_TYPE=nginx
   CHECK_SSL=true
   MIN_TLS_VERSION=1.3
   REQUIRED_HEADERS=X-Frame-Options,Content-Security-Policy
   ```

---

## Running via REST API

### Create Template with Environment Variables

```bash
curl -X POST http://localhost:8080/api/v1/job_templates/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Compliance Check",
    "description": "System compliance with custom env vars",
    "playbook": "examples/playbooks/demo_compliance.yml",
    "job_type": "run",
    "extra_vars": {
      "env_vars": {
        "CHECK_SSH": "true",
        "MIN_DISK_SPACE_GB": "20",
        "REQUIRED_PACKAGES": "vim,curl,git,docker"
      }
    }
  }'
```

### Launch Job with Override Environment Variables

```bash
# Get template ID from creation response or list templates
TEMPLATE_ID="your-template-id"

curl -X POST http://localhost:8080/api/v1/job_templates/${TEMPLATE_ID}/launch/ \
  -H "Content-Type: application/json" \
  -d '{
    "extra_vars": {
      "env_vars": {
        "MIN_DISK_SPACE_GB": "50",
        "REQUIRED_PACKAGES": "vim,curl,git,docker,kubectl"
      }
    }
  }'
```

---

## Creating Your Own Playbooks

### Using Environment Variables in Playbooks

```yaml
---
- name: My Custom Playbook
  hosts: localhost
  vars:
    # Access environment variables via lookup
    my_var: "{{ lookup('env', 'MY_VAR') | default('default_value') }}"
    check_enabled: "{{ lookup('env', 'CHECK_ENABLED') | default('true') | bool }}"
    threshold: "{{ lookup('env', 'THRESHOLD') | default('100') | int }}"
  
  tasks:
    - name: Use environment variable
      debug:
        msg: "My variable value: {{ my_var }}"
      when: check_enabled
```

### Best Practices

1. **Always provide defaults**: Use `default('value')` filter to avoid errors when env var is not set
2. **Type conversion**: Use `| bool`, `| int`, `| float` filters for proper type conversion
3. **Documentation**: Document all environment variables in your playbook comments
4. **Validation**: Add tasks to validate environment variables early in the playbook

### Example with Validation

```yaml
---
- name: Playbook with Env Var Validation
  hosts: localhost
  vars:
    api_key: "{{ lookup('env', 'API_KEY') | default('') }}"
    timeout: "{{ lookup('env', 'TIMEOUT') | default('30') | int }}"
  
  tasks:
    - name: Validate API key is set
      assert:
        that:
          - api_key | length > 0
        fail_msg: "API_KEY environment variable must be set"
    
    - name: Validate timeout range
      assert:
        that:
          - timeout >= 10
          - timeout <= 300
        fail_msg: "TIMEOUT must be between 10 and 300 seconds"
```

---

## Testing Locally

Before creating a template in the server, test your playbook locally:

```bash
# Set environment variables
export CHECK_SSH=true
export MIN_DISK_SPACE_GB=20
export REQUIRED_PACKAGES=vim,curl,git

# Run playbook
ansible-playbook examples/playbooks/demo_compliance.yml
```

---

## Troubleshooting

### Environment Variables Not Working

1. **Check the format**: Ensure `KEY=value` format with no extra spaces
2. **Check the playbook**: Verify it uses `lookup('env', 'KEY')` to access variables
3. **Check job output**: Review stderr in the Jobs page for error messages

### Playbook Not Found

- Use absolute paths: `/full/path/to/playbook.yml`
- Or use paths relative to where the server is running
- For the examples, use: `examples/playbooks/demo_compliance.yml`

### Permission Issues

Ensure the playbook file is readable by the user running the server:
```bash
chmod 644 examples/playbooks/*.yml
```

---

## Additional Resources

- [Ansible Playbook Documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks.html)
- [Ansible Environment Variables](https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html)
- [InSpec Execution Server Documentation](../../docs/SERVER.md)
