require 'rubygems'
require 'sinatra'
require 'haml'
require 'json'
require 'time'
require 'sinatra/flash'
require 'sinatra/partial'
require 'sinatra-websocket'
require 'i18n'
require 'i18n/backend/fallbacks'
require 'securerandom'
require 'dotenv'
require 'mkfifo'
require './opendoor_db'

configure do
  #set :environment, :production
  set :show_exceptions, false #if production?
  set :bind, '0.0.0.0'
  enable :logging
  register Sinatra::Partial
  set :partial_template_engine, :haml
  Dotenv.load

  # I18n settings
  I18n::Backend::Simple.send(:include, I18n::Backend::Fallbacks)
  I18n.load_path = Dir[File.join(settings.root, 'locales', '*.yml')]
  I18n.backend.load_translations
  I18n.enforce_available_locales = false
  I18n.config.available_locales = [:de, :en]
  I18n.default_locale = :de
end

configure :development do
  require "sinatra/reloader"
  set :raise_errors, true
end

helpers do
  def db_exist?
    File.exist?("/home/pi/.opendoord/opendoor.db")
  end

  def version
    "OpenDoor 2.0a"
  end

  def switch_lang(lang)
    "/#{lang.to_s}#{request.path}"
  end

  class Time
    def to_hm
      @tzo ||= Time.zone_offset(Time.now.getlocal.zone)
      (self + @tzo).strftime("%H:%M")
    end
  end

  class String
    def to_1970
      @utc_offset ||= sprintf(" %+03d00", Time.now.utc_offset/3600)
      Time.parse("1970-01-01 " + self + @utc_offset)
    end
  end

  def render_dow_row(row)
    EM.next_tick { settings.sockets.each{ |s| s.send("UPDATE DOW ROW #{row}") } }
  end

  def render_badges(dow)
    output = ''
    OpenTime.by_dow(dow).each do |dur|
      output += partial('badge', locals: {dur: dur})
    end
    output
  end

  def render_auth_codes
    output = ''
    AuthCode.all.each do |auth|
      output += partial('authcode', locals: {auth: auth})
    end
    output
  end

  def auth_with_id?(params)
    auth_id = params[:auth_id].blank? ? nil : params[:auth_id]
    authorized = AuthCode.where(auth_code: auth_id, disabled: 0).first
    authorized.nil? ? nil : authorized.user_name
  end

  def protected!
    return if authorized?
    headers['WWW-Authenticate'] = 'Basic realm="Restricted Area"'
    halt 401, "Not authorized\n"
  end

  def authorized?
    @auth ||=  Rack::Auth::Basic::Request.new(request.env)
    @auth.provided? and @auth.basic? and @auth.credentials and @auth.credentials == ['admin', (ENV['APP_PASS'] || 'baseball')]
  end

  def send_pipe_protected(cmd)
    protected!
    app_fifo = open("/tmp/app_fifo", "w")
    puts "Write pipe opened - Sending '" + cmd + "'."
    app_fifo.puts(cmd + "\n")
    app_fifo.close
    [200, {}, []]
  end

end

before '/:locale/*' do
  pass if /^\/api/.match(request.path)
  I18n.locale = params[:locale]
  request.path_info = '/' + params[:splat][0]
end

set :sockets, []
get '/' do
  protected!
#puts "Version: #{version}"
  halt "Sorry, no database yet ... please start daemon first" unless db_exist?
  @opendoor_logs = OpenDoorLog.latest_logs
  @auth_codes = AuthCode.all

  if !request.websocket?
    @title = ENV['APP_TITLE'] || 'OpenDoor'
    haml :index
  else
    request.websocket do |ws|
      ws.onopen do
        # ws.send("Hello World!")
        settings.sockets << ws
      end
      ws.onmessage do |msg|
        EM.next_tick { settings.sockets.each{ |s| s.send(msg) } }
      end
      ws.onclose do
        warn("websocket closed")
        settings.sockets.delete(ws)
      end
    end
  end
end

### Actions ###
post '/open_front_door' do
  send_pipe_protected('OPEN FRONT DOOR')
end

post '/open_apartment_door' do
  send_pipe_protected('OPEN APARTMENT DOOR')
end

post '/keep_apartment_door_open' do
  duration = params[:duration] || 2
  puts "Keep apartment open for #{duration}"
  send_pipe_protected("KEEP APARTMENT DOOR OPEN #{duration}")
end

post '/close_apartment_door' do
  puts "Close apartment door"
  send_pipe_protected("CLOSE APARTMENT DOOR")
end

post '/open_front_door_timed' do
  duration = params[:duration] || 5
  send_pipe_protected("OPEN FRONT DOOR TIMED #{duration}")
end

### Auth codes management
post '/create_auth_code' do
  protected!
  unless params[:name].blank?
    auth_code = SecureRandom.hex[0..11] # 12 digit code
    puts "Add a new authorization code '#{auth_code}' for '#{params[:name]}'"
    begin
      puts "Create Auth code and return all codes!"
      AuthCode.create!(user_name: params[:name], auth_code: auth_code)
      puts "Auth code created!"
      {html: render_auth_codes}.to_json
    rescue
      puts "Can not create auth code. User or code exists!"
      [422, {}, []]
    end
  else
    puts "Can not create auth code. User name missing!"
    [422, {}, []]
  end
end

post "/remove_auth_code" do
  protected!
  unless params[:id].blank?
    auth_entry = AuthCode.find_by_id(params[:id])
    auth_entry.destroy unless auth_entry.nil?
    {count: AuthCode.count.to_s}.to_json
  else
    puts "Can not remove auth code. User id missing!"
    [422, {}, []]
  end
end

post "/disable_auth_code" do
  protected!
  unless params[:id].blank?
    auth_entry = AuthCode.find_by_id(params[:id])
    disabled = !auth_entry.disabled?
    auth_entry.update_attributes(disabled: disabled)
    puts "Enable/disable auth code for auth: #{params[:id]} - #{disabled}."
    {disabled: disabled.to_s}.to_json
  else
    puts "Can not disable auth code. User id missing!"
    [422, {}, []]
  end
end

### Open times
get "/get_duration_by_id" do
  protected!
  id = params['id'].to_i
  unless (dur = OpenTime.find_by_id(id)).nil?
    {dur: {id: dur.id, title: dur.title, open_dow: dur.open_dow,
      open_begin: dur.open_begin.to_hm, open_end: dur.open_end.to_hm,
      open_after: dur.open_after}}.to_json
  else
    puts "Unable to find OpenTime for id=#{id}!"
    [422, {}, []]
  end
end

get "/get_durations_by_dow" do
  protected!
  dow = params['dow'].to_i
  if dow>=0 and dow<=6
    {html: render_badges(dow)}.to_json
  else
    puts "Unable to get open times (dow not in range)!"
    [422, {}, []]
  end
end

post "/create_duration" do
  protected!
  params[:open_begin] = params[:open_begin].to_1970
  params[:open_end] = params[:open_end].to_1970
  params.delete("captures")

  begin
    OpenTime.create(params)
    render_dow_row(params[:open_dow])
  rescue
    puts "Unable to create new open time!"
    [422, {}, []]
  end
end

put "/update_duration" do
  protected!
  params[:open_begin] = params[:open_begin].to_1970
  params[:open_end] = params[:open_end].to_1970
  params.delete("captures")

  begin
    ot = OpenTime.find_by_id(params[:id])
    ot.attributes = params
    render_dow_row(ot.open_dow)
    render_dow_row(ot.open_dow_was) if ot.open_dow_changed?
    ot.save!
  rescue
    puts "Unable to update existing open time!"
    [422, {}, []]
  end
end

put "/toggle_duration" do
  protected!
  puts "Toggle open time activity! #{params[:toggle]}"
  unless params[:id].blank? or params[:toggle].blank?
    ot = OpenTime.find_by_id(params[:id])
    ot.update_attributes(disabled: params[:toggle])
    render_dow_row(ot.open_dow)
  end
end

delete "/delete_duration" do
  protected!
  unless params[:id].blank?
    ot = OpenTime.find_by_id(params[:id])
    render_dow_row(ot.open_dow)
    ot.destroy
  end
end

### Logging functions
post '/clear_log' do
  protected!
  puts "Clear log!!!"
  OpenDoorLog.clear
  [200, {}, []]
end

get '/last_log' do
  protected!
  puts "Return last log entry!!!"
  last = OpenDoorLog.last
  { log: last.log_text, timestamp:  I18n.l(last.created_at, format: :short) }.to_json
end

# JSON API ###########################
# Everybody is allowed to ping the service
get '/api/v1/ping', provides: :json do
  pass unless request.accept? 'application/json'
  puts "Receive a Ping via API"
  {version: version}.to_json
end

# TODO: Implement and test
post '/api/v1/alarm', provides: :json do
puts params.inspect
  pass unless request.accept? 'application/json'
  unless (user = auth_with_id?(params)).nil?
    app_fifo = open("/tmp/app_fifo", "w")
    puts "Write pipe opened - Sending an Alarm (Open all doors - #{user})."
    app_fifo.puts("ALARM OPEN DOORS (#{user})\n")
    app_fifo.close
    [200, {}, []]
  else
    [422, {}, []]
  end
end

# curl example: 
# curl -H "Content-Type: application/json" -X POST -d '{}' \
# https://opendoor/api/v1/opendoor?auth_id=4082570ae9447
#
post '/api/v1/opendoor', provides: :json do
  pass unless request.accept? 'application/json'
  unless (user = auth_with_id?(params)).nil?
    puts "Receive an OpenDoor via API from #{user}"
    app_fifo = open("/tmp/app_fifo", "w")
    puts "Write pipe opened - Sending 'OPEN APARTMENT DOOR (#{user})'."
    app_fifo.puts("OPEN APARTMENT DOOR (#{user})\n")
    app_fifo.close
    [200, {}, []]
  else
    [422, {}, []]
  end
end

# TODO: Implement and test
# Auto open the front door for 5 minutes
# Curl example see above.
post '/api/v1/doortimer', provides: :json do
  pass unless request.accept? 'application/json'
  unless (user = auth_with_id?(params)).nil?
    app_fifo = open("/tmp/app_fifo", "w")
    puts "Write pipe opened - Sending 'OPEN DOOR TIMED 5'."
    app_fifo.puts("OPEN DOOR TIMED 5\n")
    app_fifo.close
    [200, {}, []]
  else
    [422, {}, []]
  end
end

Thread.new do # trivial example work thread
  puts "App create fifo/pipe if not available."
  unless File.exists?("/tmp/opendoor_fifo")
    File.mkfifo("/tmp/opendoor_fifo")
    File.chmod(0666, "/tmp/opendoor_fifo")
  end
  puts "App read fifo/pipe waiting to be opended ..."
  fifo = File.open("/tmp/opendoor_fifo", "r+")
  puts "Read pipe opened - Waiting for messages."
  while true do
    input = fifo.gets
    # ignore some frequent messages
    puts "App received from fifo: #{input}" if input != "NORMAL TIME\n"
    # Just forward fifo message to the web app via websocket
    EM.next_tick { settings.sockets.each{ |s| s.send(input) } }
  end
end
