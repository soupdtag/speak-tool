# init.py
# initiate connection to mturk
# used in all mturk scripts
import boto3
import argparse
import json
import os.path

def yes_no(answer):
    yes = set(['yes','y', 'ye', ''])
    no = set(['no','n'])
     
    while True:
        choice = input(answer).lower()
        if choice in yes:
           return True
        elif choice in no:
           return False
        else:
           print("Please respond with 'yes' or 'no'")
           
def init(region, profile, env):

	# user AWS credentials (--profile)
	session = boto3.Session(profile_name = profile)
	
	# sandbox vs production environment (--env)
	if env == 'production':
		print('initializing to PRODUCTION environment...')
		endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'
		preview_url = 'https://www.mturk.com/mturk/preview'
	else:
		# invalid input defaults to sandbox environment
		if env != 'sandbox': print('invalid user input for \'environment\'')

		print('initializing to SANDBOX environment...')
		endpoint_url = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
		preview_url = 'https://workersandbox.mturk.com/mturk/preview'
	
	# initiate connection using above params
	client = session.client(
		service_name='mturk', endpoint_url=endpoint_url, region_name=region)

	return client, preview_url