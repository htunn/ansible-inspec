# Environment Variables Format Examples

## Simple Format (KEY=value)

Best for simple string values:

```
API_KEY=abc123def456
DB_HOST=localhost
DB_PORT=5432
ENABLE_DEBUG=true
```

## JSON Format

Best for complex or multi-line values:

### Certificate CSR Example
```json
{
  "CERT_CSR": "-----BEGIN CERTIFICATE REQUEST-----\nMIICvDCCAaQCAQAwdzELMAkGA1UEBhMCVVMxDTALBgNVBAgMBFV0YWgxDzANBgNV\nBAcMBkxpbmRvbjEWMBQGA1UECgwNRGlnaUNlcnQgSW5jLjERMA8GA1UECwwIRGln\naUNlcnQxHTAbBgNVBAMMFGV4YW1wbGUuZGlnaWNlcnQuY29tMIIBIjANBgkqhkiG\n9w0BAQEFAAOCAQ8AMIIBCgKCAQEA8+To7d+2kPWeBv/orU3LVbJwDrSQbeKamCmo\nwp5bqDxIwV20zqRb7APof9Jj1rG0YvFn\n-----END CERTIFICATE REQUEST-----",
  "PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDz5Ojt37aQ9Z4G\n...\n-----END PRIVATE KEY-----"
}
```

### JSON Configuration Example
```json
{
  "API_CONFIG": "{\"endpoint\": \"https://api.example.com\", \"timeout\": 30, \"retries\": 3}",
  "DATABASE_CONFIG": "{\"host\": \"localhost\", \"port\": 5432, \"ssl\": true}"
}
```

### Multi-line Script Example
```json
{
  "INIT_SCRIPT": "#!/bin/bash\nset -e\necho 'Starting initialization...'\nmkdir -p /tmp/app\ncd /tmp/app\ncurl -O https://example.com/installer.sh\nchmod +x installer.sh\n./installer.sh",
  "CHECK_SCRIPT": "#!/bin/bash\nif [ -f /etc/config.yml ]; then\n  echo 'Config exists'\n  exit 0\nelse\n  echo 'Config missing'\n  exit 1\nfi"
}
```

### Base64 Encoded Data Example
```json
{
  "CERT_BASE64": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURYVENDQWtXZ0F3SUJBZ0lKQUtOTzRVMzJLVjBNTUEwR0NTcUdTSWIzRFFFQkN3VUFNRVl4Q3pBSkJnTlYKQkFZVEFsVlRNUXN3Q1FZRFZRUUlEQUpEUVRFVk1CTUdBMVVFQnd3TVUyRnVSbkpoYm1OcGMyTnZNUk13RVFZRApWUVFLREFwRmVHRnRjR3hsSUVOdk1CNFhEVEl3TURFeE1ERXdNREF3TUZvWERUSXhNREV4TURFd01EQXdNRm93ClJqRUxNQWtHQTFVRUJoTUNWVk14Q3pBSkJnTlZCQWdNQWtOQk1SVXdFd1lEVlFRSERBeFRZVzVHY21GdVkybHoKWTI4eEV6QVJCZ05WQkFvTUNrVjRZVzF3YkdVZ1EyOHdnZ0VpTUEwR0NTcUdTSWIzRFFFQkFRVUFBNElCRHdBdwpnZ0VLQW9JQkFRQ3RkVkI2c2pESGswdmRlcWJJWXFYTUpvRHVOTTJCUG1GQlVFQVJua3VTeGp6eDhTMjFHdE1kCm95bE5UYWpIQnNPa1FCcGxkR3o4RzltVm93MHQzT2VGK3RuL2N2VjlyZkFwOHVVeGlQRUpITE01bnRXNHFHc1YKMm44NUFZNW9JQllhNm5NdGlzSFhhVmE1ZkZOS2RxSFlqN2NRM1JENldQRkhOMXJ5TTd0Y1hIenNzdnZDZTdPWgpseW1hT2hxZXhMTXRDM0JsSW5zdm5FTk1kSmJrN3hHM1J5c1BpOXZuaUVQMnRDNGhueGw1aDZHUWx1aWZVYnNHCmVIbFBmT1Eza1JWTFdwRzlPb3BqcWtkY25TOU1nNUlmcHdaYWczWGFQR0hrcGNmUk0rZkhmTnQ0UzJUUHJ1VFQKaytWOE42dUthZnhISzdCZ1pWYUtFSlpoUktTdEFnTUJBQUdqVXpCUk1CMEdBMVVkRGdRV0JCVGhvVFlTRWFCdwpBZ01CQWdNRVVBMEJBZ01CQVRBZkJnTlZIU01FR0RBV2dCVGhvVFlTRWFCd0FnTUJBZ01FVUEwQkFnTUJBVEFQCkJnTlZIUk1CQWY4RUJUQURBUUgvTUEwR0NTcUdTSWIzRFFFQkN3VUFBNElCQVFCdHQxY1J6ak1saGVndzZjZWgKcTEzT1Q3QlczbHRHZEdtNjhWNTNiZndRN1BzM1JWQmdxNG1Qb0JIcGF4M0FhUWRHUDllOGw2YllDWnJlK2Vlaw==",
  "FILE_CONTENT_B64": "VGhpcyBpcyBhIHRlc3QgZmlsZSBjb250ZW50LgpJdCBjb250YWlucyBtdWx0aXBsZSBsaW5lcy4KQW5kIHNwZWNpYWwgY2hhcmFjdGVyczogJCAhIEAgIyAl"
}
```

### Mixed Complex Values Example
```json
{
  "SIMPLE_VAR": "simple_value",
  "SSL_CERT": "-----BEGIN CERTIFICATE-----\nMIIDXTCCAkWgAwIBAgIJAKNO4U32KV0MMA0GCSqGSIb3DQEBCwUAMEYxCzAJBgNV\n-----END CERTIFICATE-----",
  "CONFIG_YAML": "database:\n  host: localhost\n  port: 5432\nlogging:\n  level: INFO\n  file: /var/log/app.log",
  "DEPLOYMENT_JSON": "{\"version\": \"1.0\", \"replicas\": 3, \"resources\": {\"cpu\": \"2\", \"memory\": \"4Gi\"}}",
  "THRESHOLD": "100",
  "ENABLED": "true"
}
```

## Using in Ansible Playbooks

### Access Simple Environment Variables
```yaml
- name: Use environment variable
  debug:
    msg: "API Key is {{ lookup('env', 'API_KEY') }}"
```

### Access Multi-line Certificate
```yaml
- name: Write certificate to file
  copy:
    content: "{{ lookup('env', 'CERT_CSR') }}"
    dest: /tmp/request.csr

- name: Use certificate in openssl command
  shell: |
    echo "{{ lookup('env', 'CERT_CSR') }}" | openssl req -text -noout
```

### Decode Base64 Data
```yaml
- name: Decode and write base64 file
  shell: |
    echo "{{ lookup('env', 'FILE_CONTENT_B64') }}" | base64 -d > /tmp/output.txt
```

### Parse JSON Config
```yaml
- name: Parse JSON configuration
  set_fact:
    api_config: "{{ lookup('env', 'API_CONFIG') | from_json }}"

- name: Use parsed config
  debug:
    msg: "API endpoint: {{ api_config.endpoint }}, Timeout: {{ api_config.timeout }}"
```

## Best Practices

1. **Use Simple Format** for straightforward key-value pairs
2. **Use JSON Format** when you need:
   - Multi-line values (certificates, scripts, configs)
   - Special characters or newlines
   - Base64-encoded content
   - Nested JSON/YAML structures

3. **Escape Sequences in JSON**:
   - `\n` for newlines
   - `\"` for quotes
   - `\\` for backslashes
   - `\t` for tabs

4. **Security Considerations**:
   - Never commit sensitive data (certificates, keys) to git
   - Use secure storage or secrets management
   - Consider using Ansible Vault for sensitive playbook variables
   - Rotate credentials regularly
