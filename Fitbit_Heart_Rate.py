import json
import os
from time import sleep
import matplotlib.dates as md
import matplotlib.pyplot as plt
import pandas as pd
import requests
import glob
import rsl.json_config as json_config
from scipy.signal import savgol_filter

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


def read_alog_events(date):
    entry_list = []
    for fn in glob.glob('*_alog.txt'):
        with open(fn, 'r') as f:
            for line in f:
                if date in line:
                    entry_list.append(json.loads(line))
    return entry_list


def parse_timestamp_ignore_tz(timestamp):
    return pd.to_datetime(timestamp[:-6])


def alog_weather_data(events):
    time_axis, temperature_axis, humidity_axis = [], [], []
    for e in events:
        weather = e.get('Weather', None)
        if weather is None:
            continue
        temperature_axis.append(weather['temperature'])
        humidity_axis.append(weather['humidity'])
        time_axis.append(parse_timestamp_ignore_tz(e['time']))
    return time_axis, temperature_axis, humidity_axis


def graph_file_contents(json_filename):
    plt.figure()
    time_axis, hr_axis = json_to_data(json_filename)

    plt.xticks(rotation=25)
    ax = plt.gca()
    xfmt = md.DateFormatter('%H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    plt.plot(time_axis, hr_axis, label='raw', linewidth=1.0)
    plt.plot(time_axis, savgol_filter(hr_axis, 401, 3), label="smooth", linewidth=3.0)

    date = parse_filename_date(json_filename)
    plt.xlabel("Time")
    plt.ylabel("Heart Rate")
    plt.title(date)
    plt.legend(loc="upper left")
    plt.show()


def graph_multi_day(datelist):
    plt.figure(figsize=(18,10))
    ax = plt.gca()
    xfmt = md.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(xfmt)

    for date in datelist:
        filename = make_filename(date)
        print('Graphing %s' % (date))
        time_axis, hr_axis = json_to_data(filename)
        n = len(time_axis)
        # plt.plot(time_axis, hr_axis, label=date + ' raw', linewidth=1.0, color='cyan')

        filtered_1 = savgol_filter(hr_axis, 11, 2)
        filtered_1_min = min(filtered_1)
        filtered_1_max = max(filtered_1)
        plt.plot(time_axis, filtered_1, label=date, linewidth=1.0)
        plt.plot(time_axis, [filtered_1_min for i in range(n)], label=date, linewidth=1.0, color='gray')
        plt.plot(time_axis, [filtered_1_max for i in range(n)], label=date, linewidth=1.0, color='gray')

        events = read_alog_events(date)
        time_axis, temperature_axis, humidity_axis = alog_weather_data(events)
        plt.plot(time_axis, temperature_axis, label='Degrees F', linewidth=1.0, color='blue')
        plt.plot(time_axis, humidity_axis, label='Humidity', linewidth=1.0, color='cyan')

    title = '%s to %s' % (datelist[0], datelist[len(datelist) - 1])
    plt.xlabel("Time")
    plt.ylabel("Heart Rate")
    plt.title(title)
    plt.legend(loc="upper left")
    plt.savefig("graph.png")
    # plt.show()


def json_to_xml(json_filename):
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


def json_to_csv(json_filename):
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


def json_to_data(json_filename):
    with open(json_filename) as f:
        data = json.load(f)
    time_axis, hr_axis = [], []
    date = parse_filename_date(json_filename)
    for p in data['activities-heart-intraday']['dataset']:
        ts = pd.to_datetime('%s %s' % (date, p['time']))
        time_axis.append(ts)
        hr_axis.append(p['value'])
    return time_axis, hr_axis


def make_datelist(config):
    ts_list = pd.date_range(start=pd.to_datetime(config['Start_Date']), end=pd.to_datetime(config['End_Date'])).tolist()
    datalist = []
    for ts in ts_list:
        datalist.append(ts.strftime('%Y-%m-%d'))
    return datalist


def make_filename(date):
    return r'%s_HR_fitbit.json' % (date)


"""
References:
http://shishu.info/2016/06/how-to-download-your-fitbit-second-level-data-without-coding/
"""


def download_fitbit_data(config):
    # TODO: get OAuth Token pragmatically.
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
    datelist = make_datelist(config)

    # Fitbit API limited to 150 calls per hour.
    #
    #    (60 min/hour) * (60 sec/min) / (150 calls/hour) = 24 sec/call
    seconds_per_call = 24

    please_wait = False
    for date in datelist:
        if please_wait:
            print('\tSleeping %s seconds.' % (seconds_per_call))
            sleep(seconds_per_call)

        filename = make_filename(date)
        if os.path.exists(filename):
            print('Skipping %s, already exists' % (filename))
            please_wait = False
        else:
            url = r'%s1/user/-/activities/heart/date/%s/1d/1sec/time/00:00/23:59.json' % (config['Base_API_URI'], date)
            response = requests.get(url=url, headers={'Authorization': 'Bearer ' + config['OAuth_Token']})
            please_wait = True
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
    except FileNotFoundError:
        json_config.create_default(default_config)
        return 1

    download_fitbit_data(config)
    graph_multi_day(make_datelist(config))


if __name__ == '__main__':
    main()
