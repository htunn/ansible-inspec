# GitHub Issues Summary - ansible-inspec Critical Bugs

This directory contains three critical bug reports for the ansible-inspec project. All issues are **HIGH PRIORITY** and prevent core functionality from working properly in production environments.

## Issues Created

### 🐛 Issue 1: ARM64 Architecture Support
**File:** `issue-1-arm64-prisma.md`
**Problem:** Missing Prisma Query Engine Binary for ARM64/aarch64 Architecture
**Impact:** Database features completely broken on ARM64 Kubernetes clusters

### 🐛 Issue 2: Database Migrations
**File:** `issue-2-prisma-cli.md`  
**Problem:** Init container missing Prisma CLI - Database migrations fail silently
**Impact:** Database schema inconsistency, potential data corruption

### 🐛 Issue 3: Azure Authentication
**File:** `issue-3-azure-client-secret.md`
**Problem:** Azure AD Client Secret not exposed as environment variable
**Impact:** OAuth authentication completely non-functional

## Combined Impact

These three bugs together make the ansible-inspec Helm chart (v0.2.6) unsuitable for production use when:
- Deploying to ARM64 clusters (Issue #1)
- Using database-backed storage (Issues #1, #2)
- Requiring Azure AD authentication (Issue #3)

## How to Use

1. Copy each `.md` file content
2. Create new GitHub issues at: https://github.com/Htunn/ansible-inspec/issues
3. Paste the content into each issue
4. Add the suggested labels
5. Submit the issues

## Recommended Actions

1. ✅ Create all three GitHub issues with these details
2. 🔧 Fix in next patch release (0.2.7)
3. 🧪 Test on both x86_64 and ARM64 architectures
4. 🔍 Add integration tests for database migrations
5. ✨ Add validation for required Azure AD environment variables

**Target Release:** 0.2.7 (urgent patch release recommended)
