# script to list hits
# author: chris song

import boto3
from datetime import datetime, timezone
from init import init, yes_no
import argparse
import json

# ---------------------------------------------------------------------------------------
# print list of hits
# ---------------------------------------------------------------------------------------
def listHITs(client, logfile):

    retrieved_HITs = []

    if logfile == '':
        list_all = yes_no('No logfile provided, all existing HITs will be printed. Continue? (y/n)')
        if list_all:
            retrieved_HITs = []
            paginator = client.get_paginator('list_hits')
            for response in paginator.paginate():
                retrieved_HITs.extend(response['HITs'])
        else:
            print('Aborting')
            return
    else:
        with open(logfile, 'r') as fp:
            log_dict = json.load(fp)
        print('Retrieving %d HITs...' % len(log_dict['hit_id_to_idx'].keys()))
        print(' ')
        for HITId in log_dict['hit_id_to_idx'].keys():
            r = client.get_hit(HITId=HITId)
            retrieved_HITs.append(r['HIT'])

    print('-----------------------------------------------')
    print(' ')

    #print(retrieved_HITs)

    for item in retrieved_HITs:

        print(' HIT Id: ', item['HITId'])
        print(' GroupId:', item['HITGroupId'])
        print(' TypeId: ', item['HITTypeId'])
        print(' Status: ', item['HITStatus'])

        expiredStatus = ' Expired ' if item['Expiration'] < datetime.now(timezone.utc) else ' Active until '
        print(expiredStatus, item['Expiration'])
        print(' # assignments pending: ', item['NumberOfAssignmentsPending'])
        print(" You can view the HITs here:")
        print(' ', preview_url + "?groupId={}".format(item['HITTypeId']))
        print(' ')


# ---------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print the information for a group of HITs')
    parser.add_argument('--logfile', dest='logfile', default='', help='Print the info for the HITs in this logfile. If no file is specified, information for all existing HITs will be printed.')
    args = parser.parse_args()
    # parse config info (vars: region, profile, env, flask_url)
    with open("turk_config.txt", "r+") as config:
        for line in config: exec(line)

    # initiate connection to turk server
    client, preview_url = init(region, profile, env)

    # print list of HITs
    listHITs(client, args.logfile)
