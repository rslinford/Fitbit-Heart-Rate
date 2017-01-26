import requests
import json
import pandas as pd
from time import sleep
import rsl.json_config as json_config
 
default_config = {
   'config_file_name': r'fitbit-heart-rate.json',
   'OAuth_Client_ID': 'MyID',
   'OAuth_Client_Secret': 'MySecret',
   'OAuth_Authorization_URI': 'https://www.fitbit.com/oauth2/authorize',
   'OAuth_Token_Request_URI': 'https://api.fitbit.com/oauth2/token',
   'OAuth_Token': 'MyToken',
   'Base_API_URI': 'https://api.fitbit.com/',
   'Redirect_URI': 'http://127.0.0.1:8080/',
   'Start_Date': '2017-01-25',
   'End_Date': '2017-01-26',
}

def read_data(config):
   # TODO: get OAuth Token programmatically. 
   # For now, please generate token by hand. Use the Fitbit Tutorial page:
   #
   #     https://dev.fitbit.com/apps/oauthinteractivetutorial
   #
   # Save the resulting token in the 'fitbit-heart-rate.json' config file as the 'OAuth_Token'.

   # List of dates in yyyy-mm-dd format
   datelist = pd.date_range(start = pd.to_datetime(config['Start_Date']), end = pd.to_datetime(config['End_Date'])).tolist()

   # Fitbit API limited to 150 calls per hour.
   #
   #    (60 min/hour) * (60 sec/min) / (150 calls/hour) = 24 sec/call
   seconds_per_call = 24

   first_iteration = True
   for ts in datelist:
      if not first_iteration:
         print('\tSleeping %s seconds.' % (seconds_per_call))
         sleep(seconds_per_call)
      first_iteration = False
      date = ts.strftime('%Y-%m-%d')
      url = r'%s1/user/-/activities/heart/date/%s/1d/1sec/time/00:00/23:59.json' % (config['Base_API_URI'], date)
      filename = r'%s_HR_fitbit.json' % (date)
      response = requests.get(url=url, headers={'Authorization':'Bearer ' + config['OAuth_Token']})

      if response.ok:
         with open(filename, 'w') as f:
            f.write(response.text)
         print('Success %s' % (filename))
      else:
         print('Failed on %s, reason(%s), status(%s)' % (filename, response.reason, response.status_code))

def main():
   try:
      config = json_config.load(default_config['config_file_name'])
      json_config.normalize(config, default_config)
      read_data(config)
   except (FileNotFoundError):
      json_config.create_default(default_config)
      return 1

if __name__ == '__main__':
     main()