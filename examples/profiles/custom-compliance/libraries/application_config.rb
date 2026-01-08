# Custom resource for checking application configuration
class ApplicationConfig < Inspec.resource(1)
  name 'application_config'
  desc 'Checks application configuration files'
  example <<~EXAMPLE
    describe application_config('/etc/myapp/config.yml') do
      its('setting') { should eq 'value' }
    end
  EXAMPLE

  def initialize(path)
    @path = path
    @config = read_config
  end

  def setting(key)
    @config[key]
  end

  def exists?
    inspec.file(@path).exist?
  end

  def valid?
    exists? && !@config.empty?
  end

  private

  def read_config
    return {} unless inspec.file(@path).exist?
    
    content = inspec.file(@path).content
    require 'yaml'
    YAML.load(content) rescue {}
  end
end
