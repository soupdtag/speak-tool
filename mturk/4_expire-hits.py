# script to expire all existing hits
# author: chris song

import boto3
from datetime import datetime
from init import init, yes_no
import argparse
import json

# ---------------------------------------------------------------------------------------
# expire all HITs
# ---------------------------------------------------------------------------------------

def expireHITs(client, logfile):

	HITIds_to_expire = []

	if logfile == '':
		expire_all = yes_no('No logfile provided, all existing HITs will be expired. Continue? (y/n)')
		if expire_all:
			retrieved_HITs = []
			paginator = client.get_paginator('list_hits')
			for response in paginator.paginate():
				retrieved_HITs.extend(response['HITs'])
			print('expiring %d HITs...' % len(retrieved_HITs))
			print(' ')
			num_errors = 0
			for item in retrieved_HITs:
				HITId = item['HITId']
				HITIds_to_expire.append(HITId)
		else:
			print('Aborting')
			return
	else:
		with open(logfile, 'r') as fp:
			log_dict = json.load(fp)
			print('expiring %d HITs...' % len(log_dict['hit_id_to_idx'].keys()))
			print(' ')
			HITIds_to_expire = log_dict['hit_id_to_idx'].keys()

	num_errors = 0
	for HITId in HITIds_to_expire:
		print(' expiring HIT Id: ', HITId)
		try:
			r = client.update_expiration_for_hit(HITId=HITId,ExpireAt=0)
			print('  ... done.')
		except Exception as e:
			print(e)
			num_errors +=1

	print(' ')
	print('...done. %d errors occurred.' % num_errors)


# ---------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Expire a set of HITs')
	parser.add_argument('--logfile', dest='logfile', default='', help='Expire the HITs'
    ' in this logfile. If no file is specified, all existing HITs will be expired.')
	args = parser.parse_args()
	# parse config info (vars: region, profile, env, flask_url)
	with open("turk_config.txt", "r+") as config:
		for line in config: exec(line)

	# initiate connection to turk server
	client, preview_url = init(region, profile, env)

	# expire all HITs
	expireHITs(client, args.logfile)
