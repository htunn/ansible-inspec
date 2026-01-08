# LICENSE SUMMARY

## Project License: GPL-3.0

**ansible-inspec** is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

## Why GPL-3.0?

This project combines components from two upstream projects with different licenses:

1. **Ansible** - GPL-3.0 licensed
2. **InSpec** - Apache-2.0 licensed

When combining GPL-licensed code with Apache-2.0 licensed code, the **GPL license governs the combined work** because:

- GPL-3.0 is a **copyleft** license that requires derivative works to also be GPL-licensed
- Apache-2.0 is a **permissive** license that is **compatible** with GPL-3.0
- GPL-3.0 is more restrictive, so it takes precedence

## License Compatibility

✅ **Apache-2.0 is compatible with GPL-3.0**

The Apache License 2.0 explicitly allows incorporation into GPL-licensed projects. Section 4(b) of Apache-2.0 requires that we:
- Provide notice of modifications
- Maintain attribution

Both requirements are fulfilled through our NOTICE file and version control history.

## What This Means

### For Users
- You can use, modify, and distribute ansible-inspec under GPL-3.0 terms
- Source code must be made available
- Derivative works must also be GPL-3.0 licensed

### For Contributors
- All contributions will be licensed under GPL-3.0
- You retain copyright of your contributions
- You must ensure your contributions are GPL-compatible

### For Downstream Projects
- If you use ansible-inspec, your project must be GPL-3.0 licensed
- You must provide source code
- You must maintain license notices

## Upstream Attribution

### Ansible
- **URL**: https://github.com/ansible/ansible
- **License**: GPL-3.0
- **Copyright**: Red Hat, Inc.
- **Usage**: Inventory system, connection plugins, automation framework

### InSpec
- **URL**: https://github.com/inspec/inspec
- **License**: Apache-2.0  
- **Copyright**: Progress Software Corp. (formerly Chef Software)
- **Usage**: Compliance testing DSL, resource framework, test execution

## Files and Licenses

- `LICENSE` - Full GPL-3.0 license text with notices
- `NOTICE` - Attribution and compatibility information
- All source code - GPL-3.0
- Documentation - GPL-3.0

## References

- GPL-3.0 License: https://www.gnu.org/licenses/gpl-3.0.txt
- Apache-2.0 License: https://www.apache.org/licenses/LICENSE-2.0.txt
- GPL Compatibility: https://www.gnu.org/licenses/license-list.html#apache2

## Legal Compliance Checklist

- [x] GPL-3.0 LICENSE file included
- [x] NOTICE file with upstream attribution
- [x] Copyright notices in source files
- [x] License compatibility documented
- [x] Modification notices for Apache-2.0 components
- [x] Source code availability ensured
- [x] License headers in code files

## Questions?

For licensing questions, please:
1. Review the LICENSE and NOTICE files
2. Check the upstream project licenses
3. Consult with legal counsel if needed
4. Open a discussion on GitHub

---

**Disclaimer**: This is a summary for convenience. The actual LICENSE file contains the legally binding terms.
