# Control using standard InSpec resources
control 'basic-1' do
  impact 1.0
  title 'Ensure required packages are installed'
  desc 'System should have required packages'

  describe package('openssh-server') do
    it { should be_installed }
  end

  describe service('sshd') do
    it { should be_running }
    it { should be_enabled }
  end
end

# Control using custom resource
control 'custom-1' do
  impact 0.8
  title 'Ensure application is configured correctly'
  desc 'Application configuration should meet requirements'

  describe application_config('/etc/myapp/config.yml') do
    it { should exist }
    it { should be_valid }
    its('setting.timeout') { should cmp >= 30 }
    its('setting.debug') { should eq false }
  end
end

# Control with file checks
control 'files-1' do
  impact 1.0
  title 'Ensure critical files have correct permissions'
  desc 'System files should be properly secured'

  describe file('/etc/passwd') do
    it { should exist }
    its('mode') { should cmp '0644' }
    its('owner') { should eq 'root' }
  end

  describe file('/etc/shadow') do
    it { should exist }
    its('mode') { should cmp '0000' }
    its('owner') { should eq 'root' }
  end
end
