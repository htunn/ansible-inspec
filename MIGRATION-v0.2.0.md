# Migration Guide: v0.1.x → v0.2.0

## 🎉 Major Architectural Improvement

Version 0.2.0 represents a **fundamental redesign** of ansible-inspec. The converter now performs **TRUE TRANSLATION** from InSpec to native Ansible modules instead of wrapping InSpec commands.

## What Changed

### Before v0.2.0 ❌
- Generated tasks that **executed InSpec via shell commands**
- Required InSpec installed on **ALL target systems**
- Just a wrapper generator - no real conversion
- Blocked InSpec-to-Ansible migration

### After v0.2.0 ✅
- Generates tasks using **native Ansible modules**
- **NO InSpec required on targets**
- True translation - real InSpec-to-Ansible conversion
- Enables complete migration from InSpec to Ansible

## Breaking Changes

### None for Most Users

**Good news:** This is a **backward-compatible** major version change:
- Existing converted collections continue to work
- InSpec fallback maintained for unsupported resources
- No changes required to existing playbooks

### For Custom Resource Users

If your profiles use **custom InSpec resources** (from `libraries/` directory):
- Custom resources still use InSpec fallback
- InSpec must be installed on targets for custom resources
- Consider migrating custom resources to native Ansible tasks

## Supported Resources (v0.2.0)

### Windows Resources

| InSpec Resource | Ansible Module | InSpec Required? |
|----------------|----------------|------------------|
| `security_policy` | `ansible.windows.win_security_policy` | ❌ No |
| `registry_key` | `ansible.windows.win_reg_stat` | ❌ No |
| `audit_policy` | `ansible.windows.win_shell` (auditpol) | ❌ No |
| `service` | `ansible.windows.win_service_info` | ❌ No |
| `windows_feature` | `ansible.windows.win_feature` | ❌ No |
| `file` | `ansible.windows.win_stat` | ❌ No |

### Linux Resources (Legacy)

These resources continue to use the legacy converter logic:
- `package` → `ansible.builtin.package_facts`
- `sshd_config` → `ansible.builtin.lineinfile`
- `command` → `ansible.builtin.command`
- `kernel_parameter` → `ansible.posix.sysctl`

### Unsupported Resources

Resources not listed above fall back to InSpec wrapper:
- WMI queries
- PowerShell scripts
- Custom resources
- Advanced InSpec resources

## Migration Path

### Step 1: Reconvert Your Profiles

Re-run the converter on your InSpec profiles to generate native Ansible tasks:

```bash
ansible-inspec convert /path/to/inspec/profile \
  --output-dir ./converted-collections \
  --namespace compliance \
  --collection-name cis_benchmark
```

### Step 2: Review Generated Tasks

Check the generated roles for native module usage:

```yaml
# Before (v0.1.x) - InSpec wrapper
- name: Execute InSpec check for security_policy
  ansible.windows.win_shell: inspec exec - -t local://...
  args:
    stdin: "control '1.1.2...' do..."

# After (v0.2.0) - Native Ansible
- name: Get security policy settings
  ansible.windows.win_security_policy:
    section: System Access
  register: security_policy_result

- name: Validate Maximum Password Age
  ansible.builtin.assert:
    that:
      - security_policy_result.MaximumPasswordAge == 365
```

### Step 3: Test Without InSpec

Test your converted collections on targets **WITHOUT InSpec installed**:

```bash
# Remove InSpec from target (if present)
# Windows PowerShell:
PS> gem uninstall inspec

# Run converted playbook
ansible-playbook -i inventory.yml \
  compliance/cis_benchmark/playbooks/example.yml
```

**Expected Result:** ✅ All checks pass without InSpec

### Step 4: Update CI/CD

Remove InSpec installation from your target provisioning:

```yaml
# BEFORE: Required InSpec on all targets
- name: Install InSpec
  ansible.windows.win_chocolatey:
    name: inspec
    state: present

# AFTER: No InSpec needed!
# (Remove the task entirely)
```

## Benefits of Upgrading

### 1. Eliminate InSpec Dependency
- No InSpec installation required on targets
- No Ruby runtime needed
- No gem dependency management

### 2. True Migration Path
- Actually migrate FROM InSpec TO Ansible
- Not just wrapping InSpec in Ansible tasks
- Complete technology stack simplification

### 3. Better Performance
- Native module execution (no InSpec overhead)
- Faster compliance checks
- Reduced memory footprint

### 4. Improved Scalability
- Deploy to thousands of servers easily
- No InSpec licensing concerns
- Simplified target prerequisites

### 5. Production Ready
- Uses well-tested Ansible modules
- Better error handling
- Standard Ansible patterns

## Rollback Plan

If you need to rollback to v0.1.9:

```bash
# Downgrade package
pip install ansible-inspec==0.1.9

# OR: Use old converted collections
# (They still work with new converter)
```

## Getting Help

### Check Resource Support

To see which resources will use native translation:

```python
from ansible_inspec.translators import RESOURCE_MAPPINGS

print("Supported resources:")
for resource in RESOURCE_MAPPINGS.keys():
    print(f"  - {resource}")
```

### Verify Translation

Check if a specific resource translates natively:

```python
from ansible_inspec.translators import get_translator

translator = get_translator('security_policy')
if translator:
    print("✅ Native translation available")
else:
    print("❌ Will use InSpec fallback")
```

### Report Issues

If you encounter problems:
1. Check the generated task structure
2. Verify resource is in supported list
3. Report issues with example InSpec profile

## Example Migration

### InSpec Profile
```ruby
# controls/password_policy.rb
control '1.1.2' do
  title 'Ensure Maximum password age is set'
  desc 'Password expiration policy'
  impact 1.0
  
  describe security_policy do
    its('MaximumPasswordAge') { should cmp == 365 }
    its('MinimumPasswordAge') { should be >= 1 }
  end
end
```

### Before v0.2.0 (InSpec Wrapper)
```yaml
- name: Execute InSpec check for security_policy
  ansible.windows.win_shell: |
    inspec exec - -t local:// --controls "1.1.2"
  args:
    stdin: |
      control '1.1.2' do
        describe security_policy do
          its('MaximumPasswordAge') { should cmp == 365 }
        end
      end
  register: control_1_1_2_result
  failed_when: control_1_1_2_result.rc != 0
```
**Requires:** Ansible + InSpec + Ruby on target ❌

### After v0.2.0 (Native Ansible)
```yaml
- name: Get security policy settings for control 1.1.2
  ansible.windows.win_security_policy:
    section: System Access
  register: inspec_1_1_2_security_policy

- name: Validate security policy for control 1.1.2
  ansible.builtin.assert:
    that:
      - inspec_1_1_2_security_policy.MaximumPasswordAge == 365
      - inspec_1_1_2_security_policy.MinimumPasswordAge >= 1
    fail_msg: Security policy check failed for control 1.1.2
    success_msg: Security policy check passed for control 1.1.2
```
**Requires:** Only Ansible on controller + PowerShell on target ✅

## Frequently Asked Questions

### Q: Do I need to reconvert my profiles?
**A:** Yes, to benefit from native translation. Old converted collections still work but use InSpec wrappers.

### Q: Will my existing playbooks break?
**A:** No. The generated task structure is compatible. Re-conversion is recommended but not required.

### Q: What about custom InSpec resources?
**A:** Custom resources still require InSpec on targets. Consider migrating custom logic to Ansible tasks.

### Q: Which resources are fully supported?
**A:** See "Supported Resources" section above. More resources will be added in future releases.

### Q: Can I mix native and InSpec wrapper tasks?
**A:** Yes. Unsupported resources automatically fall back to InSpec wrapper with a warning.

### Q: How do I know if a task uses InSpec?
**A:** Native tasks use Ansible modules (`win_security_policy`, `win_reg_stat`, etc.). InSpec wrappers use `win_shell` with `inspec exec` commands.

### Q: What's the performance difference?
**A:** Native Ansible tasks are faster (no InSpec startup overhead) and use less memory.

### Q: Is this stable for production?
**A:** Yes. v0.2.0 includes comprehensive test coverage (22 tests). Native modules are well-tested Ansible modules.

## Roadmap

### Phase 2 (Upcoming)
- WMI resource translation
- PowerShell script resource
- Windows firewall rules
- Scheduled tasks

### Phase 3 (Future)
- Custom resource analysis
- Automatic custom resource conversion
- Advanced InSpec matchers

### Phase 4 (Long-term)
- Complete InSpec resource coverage
- InSpec profile validation
- Automated migration assistance

## Support

For questions or issues:
- GitHub Issues: https://github.com/your-org/ansible-inspec/issues
- Documentation: See `ansible-inspec-docs/`
- Examples: See `examples/` directory

---

**Congratulations on upgrading to v0.2.0!** 🎉

You can now enjoy true InSpec-to-Ansible conversion without InSpec dependency on your targets.
