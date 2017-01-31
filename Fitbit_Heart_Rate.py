import requests
import json
import pandas as pd
from time import sleep
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as md
from scipy.signal import savgol_filter
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
   'Start_Date': '2017-01-24',
   'End_Date': '2017-01-26',
}

def graph_it(config, json_filename):
   plt.figure()
   time_axis, hr_axis = json_to_data(config, json_filename)
 
   plt.xticks( rotation=25 )
   ax = plt.gca()
   xfmt = md.DateFormatter('%H:%M:%S')
   ax.xaxis.set_major_formatter(xfmt)
   plt.plot(time_axis, hr_axis, label="raw", linewidth=1.0)
   plt.plot(time_axis, savgol_filter(hr_axis, 301, 2), label="smooth 251", linewidth=3.0)
 
   date = parse_filename_date(json_filename)
   plt.xlabel("Time")
   plt.ylabel("Heart Rate")
   plt.title(date)
   plt.legend(loc="upper left")
   plt.show()

def json_to_xml(config, json_filename):
   with open(json_filename) as f:
      data = json.load(f)
   with open(json_filename + '.xml', 'w') as f:
      print('<hr-points>', file=f)
      for p in data['activities-heart-intraday']['dataset']:
         print('\t<point>', file=f)
         print('\t\t<time>%s</time>' % (p['time']), file=f)
         print('\t\t<value>%s</value>' % (p['value']), file=f)
         print('\t</point>', file=f)
      print('</hr-points>', file=f)

def json_to_csv(config, json_filename):
   with open(json_filename) as f:
      data = json.load(f)
   with open(json_filename + '.csv', 'w') as f:
      print(r'"Time", "Heart Rate"', file=f)
      for p in data['activities-heart-intraday']['dataset']:
         print('"%s", "%s"' % (p['time'], p['value']), file=f)

def parse_filename_date(json_filename):
   # Date expected in filename, example: '2017-01-24_HR_fitbit.json'
   date = json_filename.split('_')[0]
   return date

def json_to_data(config, json_filename):
   with open(json_filename) as f:
      data = json.load(f)
   time_axis, hr_axis = [], []
   date = parse_filename_date(json_filename)
   for p in data['activities-heart-intraday']['dataset']:
      ts = pd.to_datetime('%s %s' % (date, p['time']))
      time_axis.append(ts)
      hr_axis.append(p['value'])
   return time_axis, hr_axis

"""
References:
http://shishu.info/2016/06/how-to-download-your-fitbit-second-level-data-without-coding/
"""
def read_data(config):
   # TODO: get OAuth Token programmatically. 
   #
   # For now, please generate token by hand. Use the Fitbit Tutorial page:
   #
   #     https://dev.fitbit.com/apps/oauthinteractivetutorial
   #
   # Save the resulting token in the config file 'fitbit-heart-rate.json' as 'OAuth_Token'.
   #
   # OAuth config items currently not used:
   #    'OAuth_Client_ID'
   #    'OAuth_Client_Secret'
   #    'OAuth_Authorization_URI'
   #    'OAuth_Token_Request_URI'
   #    'Redirect_URI'

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
   except (FileNotFoundError):
      json_config.create_default(default_config)
      return 1

   #read_data(config)

   for file in glob.glob("2017*.json"):
      print(file)
      #json_to_csv(config, file)
      graph_it(config, file)

if __name__ == '__main__':
     main()
