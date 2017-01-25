import rsl.json_config as json_config

default_config = {
   'config_file_name': r'fitbit-heart-rate.json',
   "OAuth_Client_ID": "MyID",
   "Client_Secret": "MySecret",
   "OAuth_Authorization_URI": "https://www.fitbit.com/oauth2/authorize",
   "OAuth_Token_Request_URI": "https://api.fitbit.com/oauth2/token"
}

def read_data(config):
   print('TODO: implement')

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
