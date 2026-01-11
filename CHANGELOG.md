# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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


