# Example: Basic System Compliance Profile
# 
# This is an example InSpec profile for basic system compliance
# Copyright (C) 2026 ansible-inspec project contributors
# Licensed under GPL-3.0

control 'system-01' do
  impact 1.0
  title 'Operating System Check'
  desc 'Ensure the system is running a supported OS'
  
  describe os.family do
    it { should be_in ['debian', 'redhat', 'darwin'] }
  end
end

control 'system-02' do
  impact 0.8
  title 'SSH Service Configuration'
  desc 'Ensure SSH is properly configured'
  
  describe service('sshd') do
    it { should be_installed }
    it { should be_running }
    it { should be_enabled }
  end
  
  describe sshd_config do
    its('PermitRootLogin') { should eq 'no' }
    its('PasswordAuthentication') { should eq 'no' }
  end
end

control 'system-03' do
  impact 0.7
  title 'Insecure Packages Not Installed'
  desc 'Ensure insecure packages are not present'
  
  describe package('telnetd') do
    it { should_not be_installed }
  end
  
  describe package('rsh-server') do
    it { should_not be_installed }
  end
end

control 'system-04' do
  impact 0.6
  title 'File Permissions'
  desc 'Ensure important system files have correct permissions'
  
  describe file('/etc/passwd') do
    it { should exist }
    it { should be_file }
    its('mode') { should cmp '0644' }
    its('owner') { should eq 'root' }
  end
  
  describe file('/etc/shadow') do
    it { should exist }
    it { should be_file }
    its('mode') { should cmp '0000' }
    its('owner') { should eq 'root' }
  end
end
