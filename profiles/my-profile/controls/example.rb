# Example InSpec Controls for Local Profile Testing

control 'tmp-1.0' do
  impact 0.7
  title 'Verify /tmp directory exists'
  desc 'The /tmp directory must exist for temporary file storage'
  describe file('/tmp') do
    it { should exist }
    it { should be_directory }
  end
end

control 'etc-1.0' do
  impact 0.5
  title 'Verify /etc directory exists'
  desc 'The /etc directory should exist'
  describe file('/etc') do
    it { should exist }
    it { should be_directory }
  end
end

control 'root-1.0' do
  impact 0.9
  title 'Verify root user exists'
  desc 'The root user must exist on the system'
  describe user('root') do
    it { should exist }
  end
end
