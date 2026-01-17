# InSpec Profiles Directory

This directory contains local InSpec compliance profiles that can be executed by ansible-inspec.

## Structure

```
profiles/
├── my-profile/              # Example local profile
│   ├── inspec.yml          # Profile metadata
│   └── controls/           # Control files
│       └── example.rb      # Example controls
├── basic-compliance/       # Basic system compliance
├── cis-benchmark-example/  # CIS benchmark example
└── custom-compliance/      # Custom compliance checks
```

## Using Local Profiles

### In Docker Compose

The profiles directory is mounted as a read-only volume in the Docker container at `/app/profiles`.

To use a local profile in a job template:
- Set `"supermarket": false`
- Set `"profile_path": "my-profile"` (just the directory name)

Example job template:
```json
{
  "id": "local-inspec-profile",
  "profile_path": "my-profile",
  "supermarket": false,
  "target": "localhost"
}
```

### Creating Your Own Profile

1. Create a new directory:
   ```bash
   mkdir -p profiles/my-custom-profile/controls
   ```

2. Create `inspec.yml`:
   ```yaml
   name: my-custom-profile
   title: My Custom Compliance Profile
   version: 1.0.0
   supports:
     - platform: linux
   ```

3. Create controls in `controls/` directory:
   ```ruby
   control 'my-1.0' do
     impact 0.7
     title 'My custom check'
     desc 'Description of what this control checks'
     describe file('/etc/myconfig') do
       it { should exist }
     end
   end
   ```

4. Create a job template referencing your profile:
   ```json
   {
     "profile_path": "my-custom-profile",
     "supermarket": false
   }
   ```

## Chef Supermarket Profiles

To use profiles from Chef Supermarket:
- Set `"supermarket": true`
- Set `"profile_path": "owner/profile-name"` (e.g., "dev-sec/linux-baseline")

Example:
```json
{
  "profile_path": "dev-sec/linux-baseline",
  "supermarket": true
}
```

## Testing Profiles Locally

Test InSpec profiles directly using the InSpec CLI:

```bash
# Test local profile
inspec exec profiles/my-profile

# Test with specific target
inspec exec profiles/my-profile -t ssh://user@host

# Generate JSON report
inspec exec profiles/my-profile --reporter json
```

## Profile Resources

- [InSpec Profile Documentation](https://docs.chef.io/inspec/profiles/)
- [Chef Supermarket](https://supermarket.chef.io/tools?type=compliance_profile)
- [InSpec Resources Reference](https://docs.chef.io/inspec/resources/)
