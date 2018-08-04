require 'digest'
require 'sinatra/activerecord'

ActiveRecord::Base.establish_connection(
  adapter: 'sqlite3',
  database:  '/home/pi/.opendoord/opendoor.db'
)

class AuthCode < ActiveRecord::Base
end

class OpenTime < ActiveRecord::Base
  def self.by_dow(dow)
    OpenTime.where(open_dow: dow).order("open_begin ASC")
  end
end

class OpenDoorLog < ActiveRecord::Base
  def self.clear
    OpenDoorLog.delete_all
  end

  def self.latest_logs
    OpenDoorLog.order("created_at DESC").limit(15)
  end
end
