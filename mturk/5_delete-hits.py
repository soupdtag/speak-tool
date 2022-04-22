# script to delete all existing hits
# author: chris song

import boto3
from init import init, yes_no
import argparse
import json

# ---------------------------------------------------------------------------------------
# delete HITs
# ---------------------------------------------------------------------------------------
def deleteHITs(client, logfile):

	HITIds_to_delete = []

	if logfile == '':
		delete_all = yes_no('No logfile provided, all existing HITs will be deleted. Continue? (y/n)')
		if delete_all:
			retrieved_HITs = []
			paginator = client.get_paginator('list_hits')
			for response in paginator.paginate():
				retrieved_HITs.extend(response['HITs'])
			print('deleting %d HITs...' % len(retrieved_HITs))
			print(' ')
			num_errors = 0
			for item in retrieved_HITs:
				HITId = item['HITId']
				HITIds_to_delete.append(HITId)
		else:
			print('Aborting')
			return
	else:
		with open(logfile, 'r') as fp:
			log_dict = json.load(fp)
			print('deleting %d HITs...' % len(log_dict['hit_id_to_idx'].keys()))
			print(' ')
			HITIds_to_delete = log_dict['hit_id_to_idx'].keys()

	num_errors = 0
	for HITId in HITIds_to_delete:
		print(' deleting HIT Id: ', HITId)
		try:
			r = client.delete_hit(HITId=HITId)
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
	parser = argparse.ArgumentParser(description='Delete a set of HITs')
	parser.add_argument('--logfile', dest='logfile', default='', help='Delete the HITs'
    ' in this logfile. If no file is specified, all existing HITs will be deleted.')
	args = parser.parse_args()
	# parse config info (vars: region, profile, env, flask_url)
	with open("turk_config.txt", "r+") as config:
		for line in config: exec(line)

	# initiate connection to turk server
	client, preview_url = init(region, profile, env)

	# review HITs
	deleteHITs(client, args.logfile)
