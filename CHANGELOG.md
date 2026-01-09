# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

### Known Limitations
- This is a skeleton implementation
- Core integration between Ansible and InSpec not yet implemented
- Profile execution engine pending
- Test suite incomplete

### Next Steps
- Implement Ansible inventory adapter
- Implement InSpec profile executor
- Add comprehensive test suite
- Build binary distribution system
- Complete documentation

