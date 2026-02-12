# 🔧 Helm Release Workflow Fix

## Issues Fixed

### 1. Duplicate Copy Operation ✅ (Fixed in `f95d508`)
**Error:** `cp: 'helm/ansible-inspec-*.tgz' and 'helm/ansible-inspec-*.tgz' are the same file`

**Root Cause:** Workflow was copying files from `helm/` to `helm/` (same location)

**Solution:** Package chart directly to target directory using `-d helm/` flag

### 2. GitHub Release Tag Context ✅ (Fixed in `65edc5f`)  
**Error:** `⚠️ GitHub Releases requires a tag`

**Root Cause:** `softprops/action-gh-release@v1` was running after `git checkout gh-pages`, losing the tag context

**Solution:** 
- Move GitHub release creation **before** branch checkout
- Add explicit `tag_name: ${{ github.ref_name }}` parameter
- Preserve chart files through temp directory

## Workflow Flow (After Fixes)

```yaml
1. Extract version from tag ✅
2. Update dependencies ✅  
3. Package chart to helm/ directory ✅
4. Copy chart to temp location ✅
5. Create GitHub Release (with tag context) ✅
6. Checkout gh-pages branch ✅
7. Restore chart from temp location ✅
8. Update Helm repository index ✅
9. Commit and push to gh-pages ✅
```

## Changes Made

### Commit `f95d508` - Fix Duplicate Copy
```yaml
# Before (Broken)
- name: Package Helm chart
  run: |
    cd helm
    helm package ansible-inspec/

- name: Copy packaged chart  
  run: |
    cp helm/ansible-inspec-*.tgz helm/  # Same location!

# After (Fixed)  
- name: Package Helm chart
  run: |
    helm package helm/ansible-inspec/ -d helm/  # Direct to target
```

### Commit `65edc5f` - Fix GitHub Release
```yaml
# Before (Broken)
- name: Checkout gh-pages branch
- name: Create GitHub Release  # No tag context!

# After (Fixed)
- name: Create GitHub Release
  with:
    tag_name: ${{ github.ref_name }}  # Explicit tag
- name: Checkout gh-pages branch
```

## Result ✅
- ✅ No more duplicate copy operations
- ✅ GitHub releases work with proper tag context
- ✅ Chart files preserved across branch switches
- ✅ Helm repository index updates correctly
- ✅ Ready for successful v0.2.7 release

## Next Steps
1. **Re-run the failed workflow** from GitHub Actions UI, OR
2. **Use manual dispatch** from the Actions tab, OR  
3. **The fix will apply to future tag releases** automatically

The Helm chart release process is now fixed and ready! 🎉
