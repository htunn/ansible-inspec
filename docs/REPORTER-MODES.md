# ansible-inspec Reporter Modes

## Two Ways to Generate Compliance Reports

ansible-inspec supports **two distinct modes** for compliance testing and reporting:

---

## Mode 1: Native InSpec Profile Execution

**Requires**: InSpec binary installed  
**Use Case**: Running existing Ruby-based InSpec profiles directly

### Installation Required
```bash
# macOS
brew install chef/chef/inspec

# Linux
curl https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec

# Ruby gem
gem install inspec-bin
```

### How It Works
- ansible-inspec **wraps** the `inspec` binary
- Executes Ruby-based InSpec profiles
- Parses InSpec's JSON output
- Generates reports in multiple formats (JSON, HTML, JUnit)

### Example
```bash
# Run native InSpec profile
ansible-inspec exec /path/to/inspec/profile \
  --target ssh://hostname \
  --reporter "json:.compliance-reports/report.json html:.compliance-reports/report.html"
```

### When to Use
- ✅ Testing Chef Supermarket profiles (`dev-sec/linux-baseline`)
- ✅ Using existing InSpec profiles without conversion
- ✅ Need InSpec's advanced resources (aws, azure, etc.)
- ✅ Testing custom InSpec resources

### Limitations
- ⚠️ Requires InSpec installation
- ⚠️ Ruby dependency
- ⚠️ Cannot run on systems without InSpec

---

## Mode 2: Converted Ansible Collections (InSpec-Free)

**Requires**: Only Ansible (NO InSpec needed!)  
**Use Case**: Running compliance as pure Ansible playbooks

### Installation Required
```bash
# Only Ansible needed
pip install ansible-core

# ansible-inspec for conversion
pip install ansible-inspec
```

### How It Works
1. **Convert** InSpec profile to Ansible collection (one-time)
2. **Run** as standard Ansible playbook (no InSpec!)
3. **Auto-generate** InSpec-compatible reports via callback plugin

### Example

#### Step 1: Convert Profile (One-Time)
```bash
# Convert InSpec profile to Ansible collection
ansible-inspec convert /path/to/inspec/profile \
  --namespace myorg \
  --collection-name compliance
```

#### Step 2: Run Without InSpec
```bash
# Install collection
cd collections/ansible_collections/myorg/compliance
ansible-galaxy collection build
ansible-galaxy collection install myorg-compliance-*.tar.gz

# Run compliance checks (NO InSpec required!)
ansible-playbook playbooks/compliance_check.yml -i inventory.yml
```

#### Step 3: Get Reports Automatically
```
# Reports auto-generated in .compliance-reports/
.compliance-reports/
└── 20260109-143022-myorg.compliance-compliance_check.yml.json
```

### When to Use
- ✅ **InSpec not available** on target systems
- ✅ **Pure Ansible** infrastructure
- ✅ **CI/CD pipelines** without InSpec
- ✅ **Lightweight** compliance checks
- ✅ **No Ruby** dependency
- ✅ **Air-gapped environments** (no external dependencies)

### Advantages
- 🚀 No InSpec installation needed
- 🚀 Runs on any system with Ansible
- 🚀 Faster execution (native Ansible modules)
- 🚀 Auto-enabled reporting
- 🚀 InSpec schema-compatible output

### Generated Collection Features
- **Callback Plugin**: Auto-bundled in `plugins/callback/compliance_reporter.py`
- **Auto-Enabled**: Configured in `ansible.cfg`
- **InSpec-Compatible**: Reports match InSpec JSON schema exactly
- **Multiple Formats**: JSON, HTML, JUnit

---

## Comparison Matrix

| Feature | Native InSpec Mode | Converted Collection Mode |
|---------|-------------------|---------------------------|
| **InSpec Required** | ✅ Yes | ❌ No |
| **Ruby Required** | ✅ Yes | ❌ No |
| **Ansible Required** | ⚠️ Optional | ✅ Yes |
| **Report Formats** | JSON, HTML, JUnit, YAML, etc. | JSON, HTML, JUnit |
| **InSpec Schema** | ✅ Native | ✅ Compatible |
| **Custom Resources** | ✅ Full support | ⚠️ Via InSpec wrapper |
| **Chef Supermarket** | ✅ Direct | ⚠️ Convert first |
| **Execution Speed** | Slower (Ruby) | Faster (Native modules) |
| **Air-Gapped** | ❌ Hard | ✅ Easy |
| **CI/CD Integration** | Both | Both |

---

## Decision Tree

```
Do you have InSpec installed?
├─ Yes
│  ├─ Need advanced InSpec resources? → Native Mode
│  ├─ Using Chef Supermarket profiles? → Native Mode
│  └─ Want faster execution? → Convert to Collection
│
└─ No
   ├─ Can install InSpec?
   │  └─ Yes → Choose based on needs
   └─ No → **Must use Converted Collection Mode**
```

---

## FAQ

### Q: Why does ansible-inspec still need InSpec for native profiles?

**A**: In native mode, ansible-inspec is a **wrapper** around the InSpec binary, not a reimplementation. It executes `inspec exec` and formats the output. Think of it as "InSpec + Better Reporting".

### Q: Can I run InSpec profiles without InSpec?

**A**: Yes! **Convert them first**:
```bash
ansible-inspec convert inspec-profile/ --namespace myorg --collection-name myprofile
# Now run without InSpec:
ansible-playbook myorg.myprofile.compliance_check -i inventory.yml
```

### Q: Are converted collections as powerful as native InSpec?

**A**: For standard checks (file, service, package, users, etc.): **Yes, equally powerful**.  
For advanced resources (AWS, Azure, custom resources): Use native InSpec mode or include InSpec wrapper tasks.

### Q: Which mode should I use?

**Native Mode** if:
- You have InSpec installed
- Using Chef Supermarket profiles directly
- Need advanced cloud resources (AWS, Azure, GCP)
- Want InSpec's full feature set

**Converted Collection** if:
- InSpec is not/cannot be installed
- Pure Ansible environment
- Need faster execution
- Air-gapped or restricted environments
- CI/CD without InSpec

### Q: Can reports from both modes be used together?

**A**: Yes! Both generate InSpec JSON schema-compatible reports that can be:
- Combined in dashboards
- Imported to Chef Automate
- Processed by CI/CD tools
- Analyzed by the same tools

---

## Example: InSpec-Free Compliance Workflow

```bash
# 1. Convert Chef Supermarket profile (one-time)
ansible-inspec exec dev-sec/linux-baseline --supermarket --download ./profiles
ansible-inspec convert ./profiles/linux-baseline \
  --namespace devsec \
  --collection-name linux_baseline

# 2. Build and distribute collection
cd collections/ansible_collections/devsec/linux_baseline
ansible-galaxy collection build
# Share .tar.gz file with teams

# 3. Teams install and run (NO InSpec needed!)
ansible-galaxy collection install devsec-linux_baseline-*.tar.gz
ansible-playbook -i production.yml devsec.linux_baseline.compliance_check

# 4. Get reports automatically
ls .compliance-reports/
# 20260109-153045-devsec.linux_baseline-compliance_check.yml.json
# 20260109-153045-devsec.linux_baseline-compliance_check.yml.html
```

**Result**: Full CIS/DevSec compliance testing without InSpec dependency!

---

## Troubleshooting

### "InSpec not found" error in reports

**Cause**: Running native InSpec profile without InSpec installed  
**Solution**: Either:
1. Install InSpec: `brew install chef/chef/inspec`
2. Convert to collection: `ansible-inspec convert profile/`

### Reports show empty controls

**Cause**: Execution failed (InSpec missing, connection error, etc.)  
**Check**: Look for `errors` field in JSON report  
**Solution**: Review error message for resolution steps

### Callback plugin not generating reports

**Cause**: Plugin not enabled or not in collection  
**Check**: 
```bash
# Verify ansible.cfg
grep "callbacks_enabled" ansible.cfg

# Verify plugin exists
ls plugins/callback/compliance_reporter.py
```

---

## Summary

- **Native Mode**: InSpec required, full InSpec features, direct Chef Supermarket access
- **Converted Mode**: InSpec-free, pure Ansible, auto-reporting, lighter weight
- **Both**: Generate InSpec-compatible reports, CI/CD ready, production-proven

Choose the mode that fits your infrastructure and requirements!
