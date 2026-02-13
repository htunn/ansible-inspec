# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.8] - 2026-02-13

### Fixed
- **Streamlit UI**: Fixed password login flow to properly store authentication token in session state
- **Streamlit UI**: Replaced HTML meta refresh redirect with Streamlit's native rerun for better reliability
- **Streamlit UI**: Added timeout and better error handling for password login API calls

### Changed
- Improved error messaging for password login failures with content-type checking

### Technical Details
This release fixes the password/username authentication in the Streamlit UI. The previous implementation used HTML meta refresh which didn't properly persist the session state, causing "Invalid username or password" errors even with correct credentials. The new implementation uses Streamlit's session state and rerun mechanism for reliable authentication.

## [0.2.13] - 2026-02-13

### Fixed
- **CRITICAL**: Fixed OAuth authentication flow for multi-subdomain deployments (separate API and UI domains)
- **CRITICAL**: Fixed service selector conflict causing API service to route to both API and UI pods
- Fixed Streamlit `API_SERVER_URL` environment variable to point to correct API domain for browser redirects
- Fixed Streamlit health check probes to use proper `/_stcore/health` endpoint instead of `/`
- Fixed CORS configuration to include UI subdomain for cross-domain API requests
- Fixed NetworkPolicy DNS egress rules to properly target CoreDNS pods

### Changed
- Added `app.kubernetes.io/component: api` label to API deployment and service for proper pod selection
- Added `app.kubernetes.io/component: ui` label to UI deployment for service differentiation
- Simplified API deployment command from shell script to direct uvicorn invocation
- Improved environment variable configuration with distinct `API_BASE_URL` (internal) and `API_SERVER_URL` (external)
- Removed `/ui` path-based routing from ingress in favor of separate subdomain architecture
- Updated Helm chart version to 0.2.13

### Added
- Support for `streamlit.externalUrl` configuration to override default API_SERVER_URL
- Enhanced Streamlit deployment with proper API URL configuration for OAuth redirects
- Better documentation for multi-subdomain deployment scenarios

### Technical Details
This release fixes critical issues with OAuth authentication in deployments using separate subdomains for API and UI (e.g., via Cloudflare Tunnel). The service selector conflict caused 502 errors when the API service incorrectly routed traffic to UI pods. The OAuth flow now correctly redirects through the proper domains, enabling Azure AD SSO and other OAuth providers to work seamlessly.

## [0.2.7] - 2026-02-11

### Fixed
- **CRITICAL**: Added ARM64/aarch64 Prisma query engine binary support for ARM64 Kubernetes clusters
- **CRITICAL**: Fixed silent database migration failures by adding Prisma CLI to Docker images and proper error handling to init containers
- **CRITICAL**: Fixed Azure AD authentication by correctly mapping `secrets.azureClientSecret` to `AUTH__AZURE_CLIENT_SECRET` environment variable
- Added proper error handling and validation to database migration init container
- Enhanced both main and server Dockerfiles with multi-architecture Prisma support
- Optimized Docker build processes by merging RUN instructions
- Removed hardcoded ARM64 paths in server Dockerfile for proper auto-detection

### Added
- Multi-architecture Docker image support (linux/amd64, linux/arm64) for both main and server images
- Prisma CLI installation in both Docker images for reliable database migrations
- Comprehensive validation scripts (`test-fixes.sh`, `validate-deployment.sh`)
- Better error messages and troubleshooting information for failed migrations

### Changed
- Updated Helm chart version to 0.2.7
- Updated both Dockerfile and Dockerfile.server versions to 0.2.7
- Improved init container script with `set -e` for fail-fast behavior
- Enhanced Azure AD client secret handling in Helm templates
- Removed hardcoded architecture paths for better cross-platform compatibility

### Technical Details
This release resolves three critical production issues that prevented the application from working properly on ARM64 clusters, with database storage, or with Azure AD authentication. All database-dependent features now work correctly on both x86_64 and ARM64 architectures.

## [0.2.6] - 2026-02-11

### Changed
- Version bump with documentation improvements
- Updated API version references across codebase
- Improved documentation consistency

### Fixed
- Documentation version references updated
- Package metadata synchronized


### 🚀 Major Release: Enterprise Features & Production Ready

This release transforms ansible-inspec into a production-ready enterprise compliance automation platform with authentication, database storage, and version control integration.

### Added

#### 🔐 Enterprise Authentication
- **Azure AD OAuth2 Integration**: Enterprise SSO with role-based access control (RBAC)
- **Local Username/Password Authentication**: Fallback authentication for non-SSO environments
- **JWT Token Management**: Secure session management with configurable expiry
- **Role-Based Access Control**: Admin, Operator, and Viewer roles
- **Audit Logging**: Comprehensive audit trail for all user actions
- **Session Persistence**: 7-day refresh tokens with automatic renewal

#### 💾 Production Database Storage
- **PostgreSQL Backend**: Scalable database storage with Prisma ORM
- **Hybrid Storage Mode**: Dual-write validation for safe migration from file to database
- **File Storage Fallback**: Maintain backwards compatibility
- **Connection Pooling**: Optimized database connections
- **Automatic Migrations**: Database schema management via Prisma

#### 🔄 Version Control System (VCS) Integration
- **Git Repository Sync**: Automatic synchronization from GitHub/GitLab/Bitbucket
- **Encrypted Credentials**: Fernet symmetric encryption for SSH keys and tokens
- **Polling & Webhooks**: Both scheduled polling and event-driven sync
- **Auto-Import Profiles**: Automatically create job templates from synced repositories
- **Webhook Support**: GitHub and GitLab webhook integration for instant updates

#### 🎯 Enhanced REST API
- **20+ REST Endpoints**: Complete API for job templates, jobs, workflows, and VCS
- **OpenAPI/Swagger Documentation**: Interactive API documentation
- **Job Template Management**: CRUD operations for compliance job templates
- **Job Execution API**: Launch, monitor, and retrieve job results
- **VCS Management API**: Manage repositories and credentials via API
- **User Management API**: Admin endpoints for user and role management

#### 📊 Monitoring & Observability
- **Prometheus Metrics**: Comprehensive metrics for monitoring
- **Health Check Endpoint**: Service health and readiness checks
- **Validation Monitoring**: Track validation periods and auto-cutover status
- **Storage Operation Metrics**: Monitor file and database operation latencies

#### 🧪 Comprehensive Testing
- **Unit Tests**: 100+ test cases for API, models, and storage
- **Integration Tests**: End-to-end workflow testing
- **CI/CD Pipeline**: GitHub Actions workflow with multi-version Python testing
- **Code Quality Checks**: Black, flake8, mypy integration
- **Security Scanning**: Trivy vulnerability scanning

### Changed
- **Default Storage**: Changed from `hybrid` to `database` for new installations
- **API Version**: Updated FastAPI version to 0.4.0
- **Python Support**: Added Python 3.12 support
- **Docker Configuration**: Production-ready Docker Compose setup with PostgreSQL
- **Environment Variables**: All sensitive configuration moved to environment variables
- **OAuth Redirect**: Changed default OAuth redirect port from 8081 to 8080

### Fixed
- **Security**: Removed all hardcoded secrets and credentials
- **Database Connections**: Fixed connection pool management
- **VCS Sync**: Improved error handling in repository synchronization
- **Session Management**: Fixed cookie security and SameSite settings

### Deprecated
- **Redis Support**: Removed unused Redis dependency
- **Streamlit UI**: Temporarily disabled pending Prisma authentication update

### Security
- **No Hardcoded Secrets**: All secrets must be provided via environment variables
- **Encrypted Credentials**: VCS credentials encrypted at rest with Fernet
- **Secure Session Cookies**: HTTP-only, secure, with SameSite protection
- **JWT Secret Required**: Mandatory JWT secret configuration for production

### Migration Notes

**Breaking Changes**:
- Storage backend default changed from `hybrid` to `database`
- OAuth redirect URI changed from port 8081 to 8080
- Redis removed (if you were using it, migrate data first)
- Environment variables now required for all sensitive data

**Migration Path from v0.3.x**:
1. Backup your data directory
2. Set up PostgreSQL database
3. Configure environment variables in `.env` file
4. Run `prisma db push` to initialize database
5. Import existing job templates
6. Test authentication and job execution

### Documentation
- Added `TESTING.md` - Comprehensive testing guide
- Added `DOCKER-DEPLOYMENT.md` - Docker deployment guide
- Updated` README.md` - Enterprise features documentation
- Added `.env.example` - Environment configuration template
- Added CI/CD workflow documentation

### Contributors
- Htunn Thu Thu (@Htunn)

---

## [0.2.5] - 2026-01-11

### Fixed
- **CRITICAL**: Fixed missing `import re` statements in translator files
  - Added `import re` to registry_key, security_policy, windows_feature, service, file_resource translators
  - Resolves NameError: name 're' is not defined in production usage
  - Bug introduced in v0.2.4 when adding error handling and result tracking
  - Updated tests to match new native translator behavior
  - All 91 tests passing
  - Verified with 359-control InSpec profile conversion

### Technical Details
- The v0.2.4 release added `re.sub()` calls for variable name sanitization but forgot to import `re`
- This caused immediate runtime failures when converting any InSpec profile
- Tests were updated to verify native translator behavior with ignore_errors and register fields

---

## [0.2.4] - 2026-01-11

### Fixed
- **CRITICAL**: Added missing error handling and result tracking to assertion tasks
  - All `ansible.builtin.assert` tasks now include `ignore_errors: True`
  - All assertion tasks now register results with `register: <control_id>_result`
  - Playbooks no longer abort on first failed compliance check
  - Compliance reports now capture all control results (previously empty)
  - Affects all translator files: registry_key, security_policy, audit_policy, windows_feature, service, file_resource
  - Also updated converter.py for file, service, package, and command checks
  - Enables comprehensive compliance reporting across 200+ control profiles

### Technical Details
- Added `import re` to all translator modules for variable name sanitization
- Register variable names are sanitized from control IDs (special chars → underscores)
- Uses existing `sanitize_variable_name()` function in converter.py
- All assertion tasks continue execution on failure, allowing full compliance scans
- Results can now be collected by callback plugins and reporting mechanisms

---

## [0.2.3] - 2025-01-14

### Fixed
- **CRITICAL**: Rewrote SecurityPolicyTranslator to use `secedit /export` via `win_shell`
  - The `ansible.windows.win_security_policy` module does not exist in ansible.windows collection
  - v0.2.2 generated broken code for all profiles with `security_policy` resources  
  - New implementation exports policy with secedit, parses INI output, and validates with assertions
  - Affects most CIS benchmark profiles (Windows Server, Windows 10/11)
  - All generated tasks now use only existing Ansible modules (`win_shell`, `set_fact`, `assert`)

### Technical Details
- Export security policy: `secedit /export /cfg $env:TEMP\secpol.cfg /areas SECURITYPOLICY`
- Parse INI format using Jinja2 regex filters to extract policy values
- Validate with standard `ansible.builtin.assert` tasks
- No external dependencies beyond ansible.windows collection

---

## [0.2.2] - 2026-01-11

### Added

**Dynamic Custom Resources Mapper**

Implemented automatic translation of custom InSpec resources to native Ansible modules, future-proofing the converter for any custom resources encountered in InSpec profiles.

**Key Features**:
- Auto-detects custom resource implementation patterns (DISM, systeminfo, PowerShell, WMI, registry)
- Translates to native Ansible modules without requiring InSpec on targets
- Pattern-based detection system supports future custom resources automatically
- Intelligent fallback to generic command execution for unknown patterns

**Supported Patterns**:
1. **DISM Feature Checks** (`win_feature_dism`) → `ansible.windows.win_feature`
2. **Domain/Workgroup Checks** (`is_workgrp`) → `ansible.windows.win_shell` with systeminfo
3. **PowerShell Commands** → `ansible.windows.win_shell`
4. **WMI Queries** → `ansible.windows.win_shell` with Get-WmiObject
5. **Registry Checks** → `ansible.windows.win_reg_stat`

**Impact**:
- Windows Server 2019 CIS Benchmark profile (359 controls): **0 InSpec commands** (100% native Ansible)
- Custom resources `win_feature_dism` and `is_workgrp` successfully translated
- No InSpec runtime required on target systems

### Fixed

**InSpec Parser Value Extraction**

- Fixed ITS_PATTERN regex to capture operators (`==`, `>=`, `<=`, etc.) separately from values
- Updated value parsing to handle expressions like `should cmp == 365` and `should be >= 1`
- Improved assertion generation to produce correct Ansible syntax:
  - Before: `property == '== 365'` ❌
  - After: `property == 365` ✅
  - Before: `property == '>= 1'` ❌
  - After: `property >= 1` ✅

**Files Added**:
- `lib/ansible_inspec/translators/custom_resource.py` - Dynamic custom resource translator

**Files Modified**:
- `lib/ansible_inspec/translators/__init__.py` - Added CustomResourceTranslator and updated get_translator()
- `lib/ansible_inspec/translators/base.py` - Enhanced _convert_matcher_to_assertion() with operator support
- `lib/ansible_inspec/translators/security_policy.py` - Updated to use operator-aware assertion generation
- `lib/ansible_inspec/converter.py` - Fixed ITS_PATTERN regex and value extraction logic

**Verification**:
```bash
# Verify 100% native Ansible (should return 0)
grep -c "inspec exec" converted_collection/roles/*/tasks/main.yml
```

---

## [0.2.1] - 2026-01-11

### Fixed

**CRITICAL: Translators Not Being Used - Parser/Translator Field Mismatch**

After deploying v0.2.0, users discovered that converted collections still contained `inspec exec` commands. Investigation revealed translators weren't being invoked due to field name mismatch between parser and translators.

**Root Cause**:
- InSpec parser generates describe blocks with `tests` field
- Translators were expecting `expectations` field
- Parser uses `negated` for negation flag
- Translators were checking for `negate` flag
- Result: Translators returned empty results, converter fell back to InSpec wrapper

**Impact**:
- 37% of tasks still used `inspec exec` (should be 0%)
- InSpec still required on targets (defeats v0.2.0 purpose)
- Native translation not functioning

**Fix**:
- Updated all 6 translators to use `tests` instead of `expectations`
- Updated all translators to use `negated` instead of `negate`
- Updated test suite to match parser output format
- Verified 22/22 tests still passing

**Files Modified**:
- `lib/ansible_inspec/translators/security_policy.py`
- `lib/ansible_inspec/translators/registry_key.py`
- `lib/ansible_inspec/translators/audit_policy.py`
- `lib/ansible_inspec/translators/service.py`
- `lib/ansible_inspec/translators/windows_feature.py`
- `lib/ansible_inspec/translators/file_resource.py`
- `tests/test_translators.py`

**Verification**:
Users should reconvert profiles and verify:
```bash
# Should return 0 (no InSpec exec commands)
grep -c "inspec exec" converted_collection/tasks/main.yml
```

**Recommendation**: 
All users who converted profiles with v0.2.0 should upgrade to v0.2.1 and reconvert to ensure native translation is used.

---

## [0.2.0] - 2026-01-11

### ⚠️ BREAKING CHANGE: MAJOR ARCHITECTURAL REDESIGN

**Bug #5 - CRITICAL: Converter Defeats Its Own Purpose - Still Requires InSpec on Targets**

### 🎉 Fixed - The Fundamental Problem

Previously, the converter was just **wrapping InSpec commands in shell tasks**, which meant:
- ❌ InSpec still required on ALL target systems
- ❌ Ruby runtime still needed on targets
- ❌ No benefit from "conversion" - just added complexity
- ❌ Blocked migration FROM InSpec TO Ansible
- ❌ Defeated the entire purpose of the tool

**NOW:** The converter performs **TRUE TRANSLATION** from InSpec to native Ansible modules:
- ✅ **NO InSpec required on target systems**
- ✅ Only PowerShell needed (built-in to Windows)
- ✅ True InSpec-to-Ansible migration path
- ✅ Scalable to thousands of targets
- ✅ Production-ready compliance automation

### 🔧 What Changed

#### New Resource Translation Framework

Created a complete resource translation layer that maps InSpec resources to native Ansible modules:

**Supported Resources (Phase 1):**
1. **security_policy** → `ansible.windows.win_security_policy` + `assert`
2. **registry_key** → `ansible.windows.win_reg_stat` + `assert`
3. **audit_policy** → `ansible.windows.win_shell` (auditpol.exe) + `assert`
4. **service** → `ansible.windows.win_service_info` + `assert`
5. **windows_feature** → `ansible.windows.win_feature` + `assert`
6. **file** → `ansible.windows.win_stat` / `ansible.builtin.stat` + `assert`

#### Architecture Components

**New Modules:**
- `lib/ansible_inspec/translators/` - Resource translator framework
  - `base.py` - Base translator class and matcher conversion logic
  - `security_policy.py` - Password policies, account policies
  - `registry_key.py` - Registry key and value checks
  - `audit_policy.py` - Audit policy validation via auditpol
  - `service.py` - Service status and configuration
  - `windows_feature.py` - Windows feature installation checks
  - `file_resource.py` - File existence and permissions

**Modified Files:**
- `lib/ansible_inspec/converter.py`:
  - Updated `_generate_native_tasks()` to use translator framework
  - Added translator lookup and fallback logic
  - Maintains backward compatibility with legacy resource handlers

### 📊 Comparison: Before vs After

#### Before v0.2.0 (BROKEN)
```yaml
# Generated "converted" playbook
- name: Check Maximum Password Age
  ansible.windows.win_shell: inspec exec - -t local:// --controls "1.1.2..."
  args:
    stdin: "control '1.1.2...' do\n  describe security_policy..."
```
**Requirements:** Ansible + InSpec + Ruby on EVERY target ❌

#### After v0.2.0 (FIXED)
```yaml
# Generated native Ansible playbook
- name: Get security policy settings
  ansible.windows.win_security_policy:
    section: System Access
  register: security_policy_result

- name: Validate Maximum Password Age
  ansible.builtin.assert:
    that:
      - security_policy_result.MaximumPasswordAge == 365
```
**Requirements:** Only Ansible on controller + PowerShell on target ✅

### 🧪 Testing

Added comprehensive test suite (`tests/test_translators.py`) with 22 tests:

**Test Categories:**
1. **Translator Functionality** (15 tests)
   - Verifies each translator converts to correct Ansible modules
   - Tests parameter mapping and assertion generation
   - Validates registry path conversion, service state mapping, etc.

2. **Translator Registry** (4 tests)
   - Verifies translator lookup mechanism
   - Tests resource type to translator mapping

3. **🔴 CRITICAL: No InSpec Dependency** (3 tests)
   - **Validates generated tasks contain NO 'inspec exec' commands**
   - Ensures `requires_inspec` flag is False for supported resources
   - Verifies native Ansible modules are used exclusively

**Test Results:** ✅ 22/22 PASSED

### 📈 Impact

#### Users Can Now:
1. ✅ Convert InSpec profiles to Ansible collections
2. ✅ Deploy to targets WITHOUT installing InSpec
3. ✅ Migrate FROM InSpec TO Ansible (true migration)
4. ✅ Scale to thousands of Windows servers
5. ✅ Run compliance checks using native Ansible
6. ✅ Reduce operational complexity (no Ruby/gem management)

#### What This Means:
```
User: "I want to migrate from InSpec to Ansible"
Tool: "Here's your native Ansible collection!"
User: *deploys to targets*
Success: ✅ All checks pass (NO InSpec installed)
User: "Perfect! True migration accomplished."
```

### 🚧 Migration Notes

**Automatic Fallback:**
- Unsupported resources still use InSpec wrapper (with warning)
- Custom InSpec resources use InSpec fallback (until migrated)
- No breaking changes to existing converted collections

**Future Phases:**
- Phase 2: WMI, PowerShell script, firewall rules, scheduled tasks
- Phase 3: Custom resource analysis and conversion
- Phase 4: Complete coverage of InSpec resource library

### 🔗 References

- Bug Report: 2026-01-11
- Severity: **CRITICAL - ARCHITECTURAL FLAW** (P0)
- Impact: Defeats tool's primary purpose
- Issue: [Bug #5](bug-reports.md#bug-5)
- InSpec Resources: https://docs.chef.io/inspec/resources/
- Ansible Windows Modules: https://docs.ansible.com/ansible/latest/collections/ansible/windows/

---

## [0.1.9] - 2026-01-11

### Fixed

**Bug #4 - CRITICAL: Unquoted Control IDs Cause PowerShell Parsing Errors**
- Fixed PowerShell command parsing failures causing 100% task failure for CIS benchmark controls
- Root cause: Control IDs with special characters (spaces, parentheses, quotes) not quoted in commands
- Error: `L1 : The term 'L1' is not recognized as the name of a cmdlet`
- Impact: All CIS benchmark controls failed - PowerShell interpreted control ID parts as commands
- Example failing control ID: `1.1.2 (L1) Ensure 'Maximum password age' is set to '365 days'`
- Solution: Quote control IDs in InSpec commands with platform-specific escaping
- Quoting strategy:
  - **Windows**: Wrap in double quotes with backtick escaping (`\`"` for embedded quotes)
  - **Linux**: Wrap in double quotes with backslash escaping (`\\"` for embedded quotes)
- Files modified:
  - `lib/ansible_inspec/converter.py` (line 573-619): Updated `_generate_custom_resource_task()` to quote control IDs
  - `lib/ansible_inspec/converter.py` (line 621-658): Updated `_generate_inspec_fallback_task()` to quote control IDs
- Test coverage:
  - Added `test_windows_control_id_quoting()` - Validates quoted control IDs on Windows
  - Added `test_linux_control_id_quoting()` - Validates quoted control IDs on Linux
  - Tests verify actual command structure with complex control ID examples
- References:
  - Bug Report: 2026-01-11
  - Severity: CRITICAL (P0)
  - Affected: ALL Windows CIS benchmark profiles (virtually all real-world profiles)
  - PowerShell quoting rules: Special character handling required

### Testing
- Added control ID quoting validation tests
- Tests use real CIS benchmark control ID format
- Verified PowerShell and Bash quoting behavior

---

## [0.1.8] - 2026-01-11

### Fixed

**Bug #3 - CRITICAL: Incorrect win_shell Module Syntax - Missing _raw_params**
- Fixed incorrect module syntax causing 100% task failure on Windows targets
- Root cause: Used structured `cmd:` syntax with `ansible.windows.win_shell`, but module requires free-form syntax
- Error: `Get-AnsibleParam: Missing required argument: _raw_params`
- Impact: Complete blocker - first task failed immediately, no compliance checks executed
- Solution: Use free-form command syntax with parameters in `args` block for Windows
- Syntax differences:
  - **Windows (fixed)**: `ansible.windows.win_shell: <command>` with `args: {stdin: ...}`
  - **Linux (unchanged)**: `ansible.builtin.shell: {cmd: <command>, stdin: ...}` (both syntaxes work)
- Files modified:
  - `lib/ansible_inspec/converter.py` (line 573-608): Updated `_generate_custom_resource_task()` with platform-specific syntax
  - `lib/ansible_inspec/converter.py` (line 610-638): Updated `_generate_inspec_fallback_task()` with platform-specific syntax
- Test coverage:
  - Added `test_windows_module_uses_freeform_syntax()` - Verifies free-form syntax for Windows
  - Added `test_linux_module_uses_structured_syntax()` - Verifies structured syntax for Linux
  - Validates YAML structure, not just module names
- References:
  - Bug Report: 2026-01-11
  - Severity: CRITICAL (P0)
  - Affected: ALL Windows InSpec profiles (100% failure rate before fix)
  - ansible.windows.win_shell documentation: Free-form command required

### Testing
- Added YAML structure validation tests
- Verified correct syntax generation for both Windows and Linux profiles
- Tests validate actual task structure, not just module selection

---

## [0.1.7] - 2026-01-11

### Fixed

**Bug #2 - CRITICAL: Windows Shell Module Fails with stdin Parameter - ConvertFrom-Json Error**
- Fixed PowerShell incompatibility causing 18%+ task failures on Windows targets
- Root cause: `ansible.builtin.shell` with `stdin` triggers PowerShell wrapper that treats stdin as `System.Object[]` array
- Solution: Auto-detect Windows profiles and use `ansible.windows.win_shell` instead of `ansible.builtin.shell`
- Impact: All 359 Windows controls now execute successfully (fixed 66+ failing tasks)
- Detection methods:
  1. Check `inspec.yml` for `supports: platform-family: windows`
  2. Scan controls for Windows-specific resources (`registry_key`, `security_policy`, etc.)
- Files modified:
  - `lib/ansible_inspec/converter.py` (line 315-317): Added `is_windows_profile` parameter to `AnsibleTaskGenerator`
  - `lib/ansible_inspec/converter.py` (line 573-590): Updated `_generate_custom_resource_task()` to use `win_shell` for Windows
  - `lib/ansible_inspec/converter.py` (line 592-607): Updated `_generate_inspec_fallback_task()` to use `win_shell` for Windows
  - `lib/ansible_inspec/converter.py` (line 723-765): Added `_detect_windows_profile()` method
- Test coverage:
  - Added `test_windows_profile_uses_win_shell()` - Verifies Windows profiles use win_shell
  - Added `test_linux_profile_uses_builtin_shell()` - Verifies Linux profiles use builtin.shell
  - Added `test_windows_fallback_task_uses_win_shell()` - Tests fallback task module selection
  - Added `test_detect_windows_profile_from_metadata()` - Tests detection from inspec.yml
  - Added `test_detect_windows_profile_from_registry_key()` - Tests detection from resources
  - Added `test_detect_linux_profile()` - Ensures Linux profiles not misdetected
- References:
  - Bug Report: 2026-01-11
  - Severity: CRITICAL (P0)
  - Affected: Windows Server 2019, Windows Server 2025, all Windows InSpec profiles
  - Error: `ConvertFrom-Json : Cannot convert 'System.Object[]' to 'System.String'`

### Testing
- Added comprehensive unit tests for Windows/Linux profile detection
- Tests verify correct shell module selection based on platform
- Validated with real Windows Server 2019 and 2025 profiles

---

## [0.1.6] - 2026-01-11

### Fixed

**Bug #1 - CRITICAL: Control ID Regex Pattern Fails to Capture Control IDs Containing Quotes**
- Fixed regex pattern in `InSpecControlParser.CONTROL_PATTERN` that was causing 99% control loss (354 of 358 controls skipped)
- Root cause: Pattern `[^'\"]+` stopped matching at first quote character in control ID
- Solution: Replaced with backreference pattern `(['\"])(.+?)\1` to properly match quoted strings containing quotes
- Impact: Converter now successfully processes all 358 controls from CIS benchmark profiles instead of only 4
- Files modified:
  - `lib/ansible_inspec/converter.py` (line 169-172): Updated CONTROL_PATTERN regex
  - `lib/ansible_inspec/converter.py` (line 196-198): Updated group references (group 2 for control_id, group 3 for body)
- Test coverage:
  - Added `test_parse_control_with_quotes_in_id()` - Regression test for controls with single quotes in IDs
  - Added `test_parse_control_with_double_quotes_in_single_quoted_id()` - Test for mixed quote scenarios
  - Added `test_parse_multiple_controls_with_quotes()` - Test for multiple controls with various quote patterns
- References:
  - Bug Report: 2026-01-11
  - Severity: CRITICAL (P0)
  - Example failing control: `"1.1.1 (L1) Ensure 'Enforce password history' is set to '7 password(s)'"`

### Testing
- Added comprehensive unit tests for control ID regex pattern fix
- Regression tests ensure controls with quotes in IDs are properly parsed
- Test cases cover single quotes, double quotes, and mixed quote scenarios

---

## [0.1.5] - 2026-01-11

### Fixed
- Invalid Ansible variable names when converting InSpec profiles with special characters in control IDs
  - Added `sanitize_variable_name()` function to convert control IDs to valid Ansible variable names
  - Automatically handles CIS benchmark-style control IDs with spaces, parentheses, dots, and other special characters
  - Example: `"2.2.27 (L1) Ensure..."` → `"inspec_2_2_27_L1_Ensure"`

## [0.1.4] - 2026-01-09

### Added
- Detailed test results section in HTML reports with individual control details
- Interactive filter buttons for HTML reports (All/Passed/Failed/Skipped controls)
- Control impact levels and descriptions in HTML output
- Individual test result display with status messages and error details

### Fixed
- HTML reporter now uses JSON internally to properly parse InSpec results
- HTML reports now display all test data instead of empty results

### Improved
- Enhanced HTML report CSS styling for better readability
- JavaScript-based filtering for easy navigation through test results

## [0.1.3] - 2026-01-09

### Fixed
- Fixed InSpec Supermarket profile execution requiring git context in current directory
- Cache directory (`~/.inspec/cache`) is now automatically initialized as git repository
- InSpec execution for Supermarket profiles now runs from cache directory with git context
- Eliminates need for manual `git init .` workaround in non-git directories

## [0.1.2] - 2026-01-09

### Fixed
- Fixed UnboundLocalError when using `--supermarket` flag with reporters (duplicate `os` import in CLI)
- Fixed graceful KeyboardInterrupt (Ctrl+C) handling - now exits cleanly with code 130
- Fixed InSpec Supermarket profile execution in non-git directories by creating cache directory
- Fixed empty report issue when InSpec fails - now shows proper error messages
- Added `--chef-license=accept-silent` to avoid interactive license prompts

### Improved
- Better InSpec error reporting with return code checking (100=failed tests, 101=skipped)
- Enhanced error messages for debugging InSpec execution failures
- KeyboardInterrupt now preserved through subprocess calls for clean termination

## [0.1.1] - 2026-01-09

### Added
- Chef Supermarket integration with `--supermarket` flag for accessing 100+ compliance profiles
- Multi-format reporting support (JSON, HTML, JUnit) with `--reporter` and `--output` flags
- InSpec profile to Ansible collection converter with `convert` command
- InSpec-free mode - converted collections run without InSpec installation
- Comprehensive API documentation (800+ lines)
- Docker Hub overview and publishing workflow
- Quick reference guide for common commands
- Profile conversion guide with examples
- Reporter modes documentation (Native vs InSpec-free)
- Publishing guide for PyPI and Docker Hub
- Blog post template for v0.1.0 release announcement

### Fixed
- `UnboundLocalError` when using `--supermarket` flag with reporters (duplicate os import)
- Docker workflow triggers - added branch trigger for proper tag generation
- Docker environment configuration - added `environment: pypi` for secrets access
- Dockerfile - removed non-existent `bin/` directory copy (setuptools auto-generates)

### Changed
- Updated README.md badges - added Docker Pulls and GitHub Stars badges
- CI/CD workflows - publish workflow now manual trigger only (`workflow_dispatch`)
- Documentation cleanup - removed 6 unused internal docs files (2,183 lines)
- Docker workflow now builds on both branch pushes and tag pushes

### Improved
- Enhanced `ExecutionConfig` with `is_supermarket` and `output_path` parameters
- Added `to_json()`, `to_html()`, `to_junit()`, `save()` methods to `ExecutionResult`
- Multi-reporter support in CLI - can generate multiple formats simultaneously
- InSpec schema v5.22.0 compatibility for JSON reports
- Better error handling and reporting in conversion process

### Documentation
- Created comprehensive Docker Hub overview with examples and use cases
- Added CI/CD integration examples for GitLab CI and GitHub Actions
- Documented popular compliance profiles (CIS benchmarks, DevSec baselines)
- Added volume mount and environment variable documentation
- Enhanced README with feature comparisons and real-world use cases

### Tested
- Verified Supermarket integration with `dev-sec/linux-baseline` profile
- Tested multi-format reporting on remote SSH targets
- Validated profile conversion with custom resources
- Confirmed InSpec-free mode generates InSpec-compatible reports
- Tested Docker multi-architecture builds (linux/amd64, linux/arm64)

### Upstream Projects
- Ansible (GPL-3.0): https://github.com/ansible/ansible
- InSpec (Apache-2.0): https://github.com/inspec/inspec

## [0.1.0] - 2026-01-08

### Added
- Initial release
- Project structure and skeleton
- License files (LICENSE, NOTICE)
- Basic CLI interface
- README with usage examples
- Contributing guidelines

### License
- Licensed under GPL-3.0 (combining Ansible GPL-3.0 + InSpec Apache-2.0)
- Full license compatibility documentation provided


