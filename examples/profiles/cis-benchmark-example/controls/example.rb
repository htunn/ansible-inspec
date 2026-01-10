control '2.2.27 (L1) Ensure Enable computer and user accounts to be trusted for delegation is set to Administrators (DC only)' do
  impact 1.0
  title '(L1) Ensure Enable computer and user accounts to be trusted for delegation is set to Administrators (DC only)'
  desc 'This policy setting allows users to change the Trusted for Delegation setting on a computer object in Active Directory.'
  
  describe registry_key('HKLM\System\CurrentControlSet\Services\LanManServer\Parameters') do
    it { should exist }
    its('RestrictNullSessAccess') { should eq 1 }
  end
end

control '2.3.1.1 (L1) Ensure Accounts: Administrator account status is set to Disabled' do
  impact 1.0
  title '(L1) Ensure Accounts: Administrator account status is set to Disabled'
  desc 'This policy setting enables or disables the Administrator account during normal operation.'
  
  describe user('Administrator') do
    it { should exist }
  end
end

control 'test-1.2.3' do
  impact 0.5
  title 'Test with version number in ID'
  desc 'Control ID contains dots like version numbers'
  
  describe file('/etc/passwd') do
    it { should exist }
  end
end
