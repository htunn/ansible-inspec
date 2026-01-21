# Azure AD Authentication - Quick Start Guide

## 🚀 Services Running

After running `docker-compose up -d --build`, you'll have:

- **API Server**: http://localhost:8080
- **Streamlit UI**: http://localhost:8081
- **PostgreSQL**: localhost:5432
- **API Docs**: http://localhost:8080/docs

## ✅ Azure AD Configuration (Already Set)

Your `.env` file has been configured with:

```bash
AUTH__ENABLED=true
AUTH__AZURE_TENANT_ID=d85c7887-373c-4ca2-8f6a-f933178bce43
AUTH__AZURE_CLIENT_ID=aa0b0f6e-dfe8-46b1-b2e1-3365406ffc87
AUTH__OAUTH_REDIRECT_URI=http://localhost:8080/api/v1/auth/callback
AUTH__STREAMLIT_UI_URL=http://localhost:8081
```

## 🧪 Testing Authentication

### Option 1: Streamlit UI (Easiest)

1. **Open Streamlit**: http://localhost:8081
2. **Click "Login with Azure AD"**
3. **Complete Azure AD authentication**
4. **You'll be redirected back** with an active session
5. **Browse the UI** - all API calls now include your token

### Option 2: API Direct Testing

1. **Start login flow**:
   ```bash
   curl -L http://localhost:8080/api/v1/auth/login
   ```

2. **Open the redirect URL in browser** and complete Azure AD login

3. **Copy the `access_token`** from the callback URL

4. **Test authenticated endpoint**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
        http://localhost:8080/api/v1/auth/me
   ```

### Option 3: Swagger UI

1. **Open API Docs**: http://localhost:8080/docs
2. **Click "Authorize"** button (top right)
3. **Test auth endpoints** interactively

## 🔍 Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ui
docker-compose logs -f postgres
```

### Check Service Health
```bash
# API health check
curl http://localhost:8080/health

# Database health
docker-compose exec postgres pg_isready -U ansibleinspec

# Run test script
./test-auth.sh
```

## 🎯 What to Test

### 1. Login Flow
- [ ] Redirect to Azure AD works
- [ ] Azure AD login completes successfully
- [ ] Token received in callback
- [ ] User info endpoint returns data

### 2. Streamlit UI
- [ ] Login page shows when not authenticated
- [ ] Azure AD login button works
- [ ] Redirect back to Streamlit works
- [ ] Token stored in session
- [ ] User info shown in sidebar
- [ ] Logout button works

### 3. API Endpoints
- [ ] Unauthenticated requests get 401
- [ ] Valid token grants access
- [ ] Token expiry handled correctly
- [ ] RBAC roles enforced

### 4. Token Validation
- [ ] JWKS signature verification works
- [ ] Expired tokens rejected
- [ ] Invalid tokens rejected
- [ ] User claims extracted correctly

## 🐛 Troubleshooting

### "Authentication not enabled"
```bash
# Check .env
grep AUTH__ENABLED .env  # Should be true

# Restart services
docker-compose restart api ui
```

### "Cannot connect to API"
```bash
# Check if containers are running
docker-compose ps

# Check API logs
docker-compose logs api | tail -50
```

### "Database connection failed"
```bash
# Check database is ready
docker-compose exec postgres pg_isready

# Restart database
docker-compose restart postgres

# Wait for health check
docker-compose ps postgres
```

### "Redirect URI mismatch"
Make sure Azure AD app registration has:
- Redirect URI: `http://localhost:8080/api/v1/auth/callback`
- Type: Web (not SPA)

### "Invalid signature" errors
```bash
# Check JWKS caching - should auto-refresh every 24h
# Restart API to force JWKS refresh
docker-compose restart api
```

## 🔄 Useful Commands

```bash
# Rebuild and restart everything
docker-compose up -d --build

# Restart just API (after code changes)
docker-compose restart api

# View real-time logs
docker-compose logs -f api ui

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Access database
docker-compose exec postgres psql -U ansibleinspec -d ansibleinspec

# Run migrations
docker-compose exec api python -m prisma db push
```

## 📊 Expected Behavior

### Successful Login Flow:
1. User opens http://localhost:8081
2. Sees "Login with Azure AD" button
3. Clicks button → redirects to Azure AD
4. Completes Azure AD authentication
5. Redirects to http://localhost:8081/?access_token=...&token_type=bearer
6. Streamlit captures token from query params
7. Stores in `st.session_state`
8. Clears query params
9. Shows authenticated UI with user info
10. All API calls include `Authorization: Bearer` header

### API Response Examples:

**Login endpoint:**
```bash
$ curl http://localhost:8080/api/v1/auth/login
# Returns 302 redirect to Azure AD
```

**User info (authenticated):**
```bash
$ curl -H "Authorization: Bearer YOUR_TOKEN" \
       http://localhost:8080/api/v1/auth/me

{
  "id": "uuid-here",
  "username": "user@domain.com",
  "email": "user@domain.com",
  "name": "User Name",
  "roles": ["viewer"],
  "active": true
}
```

**Unauthenticated request:**
```bash
$ curl http://localhost:8080/api/v1/jobs/

{
  "detail": "Missing authentication credentials"
}
```

## ✨ Features Ready

- ✅ Azure AD OAuth2 integration
- ✅ JWT token creation and validation
- ✅ JWKS signature verification (24h cache)
- ✅ Streamlit UI with login/logout
- ✅ Role-based access control (RBAC)
- ✅ Session management
- ✅ Token refresh (via re-login)
- ✅ User database sync

## 🎉 Success Indicators

You'll know it's working when:

1. **Login redirects to Azure AD** ✓
2. **Token received after authentication** ✓
3. **Streamlit shows user info in sidebar** ✓
4. **API endpoints return data (not 401)** ✓
5. **Logs show "Authenticated user: user@domain.com"** ✓

## 🔗 Resources

- API Documentation: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- Deployment Guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Implementation Details: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

**Ready to test!** 🚀

Start with the Streamlit UI at http://localhost:8081 and click "Login with Azure AD".
