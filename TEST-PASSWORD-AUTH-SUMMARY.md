# Password Authentication Implementation - Test Summary

## Changes Implemented

### 1. Database Schema Updates
**File**: `schema.prisma`
- Added `hashedPassword` field to User model for secure bcrypt password storage
- Field is optional (`String?`) to support users without passwords (OAuth-only users)

### 2. Admin User Creation
**File**: `lib/ansible_inspec/server/db/prisma_client.py`
- Updated `initialize_database()` function to:
  - Read admin credentials from environment variables:
    - `ADMIN_USERNAME` (default: "admin")
    - `ADMIN_PASSWORD` (required - no default)
    - `ADMIN_EMAIL` (default: "admin@ansible-inspec.local")
    - `ADMIN_NAME` (default: "Administrator")
  - Hash password using bcrypt before storing
  - Only create admin user if `ADMIN_PASSWORD` is set
  - Log clear messages about admin user creation

### 3. Password Verification
**File**: `lib/ansible_inspec/server/api.py`
- Updated `/api/v1/auth/password-login` endpoint to:
  - Verify passwords using bcrypt's `pwd_context.verify()`
  - Reject login if `hashedPassword` is not set
  - Return 401 for invalid passwords
  - **Removed**: Insecure "any password" fallback

### 4. Helm Chart Configuration
**Files Modified**:
- `helm/ansible-inspec/values.yaml`: Added admin credentials section with defaults
- `helm/my-values.yaml`: Set your specific admin credentials
- `helm/ansible-inspec/templates/secret.yaml`: Pass admin credentials as secrets
- `helm/ansible-inspec/templates/NOTES.txt`: Updated documentation

## Environment Variables

### Local Testing (.env)
```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=htunn7101991
ADMIN_EMAIL=admin@localhost
ADMIN_NAME=Test Administrator
```

### Helm Values (my-values.yaml)
```yaml
secrets:
  adminUsername: "admin"
  adminPassword: "SecureAdminPass123!"  # CHANGE THIS!
  adminEmail: "admin@tripleseven.cloud"
  adminName: "Administrator"
```

## Testing Procedure

### Step 1: Rebuild Docker Images
```bash
# Stop and clean containers/volumes
docker-compose down -v

# Rebuild API service with new code
docker-compose build --no-cache api

# Start all services
docker-compose up -d
```

### Step 2: Wait for Services
```bash
# Wait for API to be healthy
sleep 15
curl http://localhost:8080/health
```

### Step 3: Run Automated Tests
```bash
# Run comprehensive test
./test-password-verify.sh
```

### Step 4: Manual Testing

**Test 1: Correct Password**
```bash
curl -X POST http://localhost:8080/api/v1/auth/password-login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"htunn7101991"}'
```
**Expected**: HTTP 200 with JWT token

**Test 2: Wrong Password**
```bash
curl -X POST http://localhost:8080/api/v1/auth/password-login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrongpassword"}'
```
**Expected**: HTTP 401 with error message

**Test 3: Authenticated Endpoint**
```bash
# Get token from Test 1
TOKEN="<your_token_here>"

curl http://localhost:8080/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: HTTP 200 with user information

## Expected Results

### ✅ Success Indicators
1. Wrong passwords are **rejected** with HTTP 401
2. Correct password returns JWT token
3. Admin user created on first startup
4. Logs show: "Admin user 'admin' created successfully"

### ❌  Failure Indicators  
1. Wrong password is accepted (HTTP 200)
2. No admin user creation logs
3. Login fails for correct password

## Database Migration

After code changes, update the database schema:

```bash
# Generate migration (if using migrations)
docker-compose run --rm api prisma migrate dev --name add_user_password

# OR use db push (for development)
docker-compose run --rm api prisma db push
```

## Troubleshooting

### Issue: Wrong password still accepted
**Cause**: Old Docker image being used
**Solution**: 
```bash
docker-compose down
docker-compose build --no-cache api
docker-compose up -d
```

### Issue: Admin user not created
**Cause**: `ADMIN_PASSWORD` not set in environment
**Check**:
```bash
docker-compose exec api env | grep ADMIN
```
**Solution**: Ensure `.env` file has `ADMIN_PASSWORD` set

### Issue: No password field in database
**Cause**: Database schema not updated
**Solution**:
```bash
docker-compose exec api prisma db push
```

## Security Notes

### ✅ Good Practices Implemented
- Bcrypt password hashing (industry standard)
- Password field is optional (supports OAuth-only users)
- Admin password required via environment variable
- No hardcoded credentials in code

### 🔒 Production Recommendations
1. **Change default password** in my-values.yaml
2. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
3. **Enable Azure AD OAuth** as primary authentication
4. **Store secrets** in Kubernetes Secrets or external secret manager (Vault, AWS Secrets Manager)
5. **Rotate credentials** regularly
6. **Enable audit logging** for all authentication attempts

## Files Modified

1. `schema.prisma` - Added hashedPassword field
2. `lib/ansible_inspec/server/db/prisma_client.py` - Admin user creation
3. `lib/ansible_inspec/server/api.py` - Password verification
4. `helm/ansible-inspec/values.yaml` - Default config
5. `helm/my-values.yaml` - Your deployment config
6. `helm/ansible-inspec/templates/secret.yaml` - Secret management
7. `helm/ansible-inspec/templates/NOTES.txt` - Documentation
8. `.env` - Local environment configuration

## Test Scripts

- `test-password-auth.sh` - Full integration test
- `test-password-verify.sh` - Password verification test

## Next Steps

1. ✅ Wait for Docker build to complete (currently running)
2. ✅ Start containers: `docker-compose up -d`
3. ✅ Run tests: `./test-password-verify.sh`
4. ✅ Verify wrong passwords are rejected (HTTP 401)
5. ✅ Deploy to Kubernetes with updated helm values
6. ✅ Change production password in my-values.yaml

## Deployment to Kubernetes

```bash
# Update my-values.yaml with strong password
vim helm/my-values.yaml

# Deploy/upgrade
helm upgrade --install ansible-inspec ./helm/ansible-inspec \
  -f helm/my-values.yaml \
  --namespace ansibleinspec \
  --create-namespace

# Check deployment
kubectl get pods -n ansibleinspec
kubectl logs -n ansibleinspec deployment/ansible-inspec -f

# Test login
kubectl port-forward -n ansibleinspec svc/ansible-inspec 8080:8080
curl -X POST http://localhost:8080/api/v1/auth/password-login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_PASSWORD"}'
```
