# script to list all submissions from HITs
# author: chris song

import boto3, xmltodict, json, os
from init import init, yes_no
import argparse
import json

# ---------------------------------------------------------------------------------------
# retreive and print review of hits
# ---------------------------------------------------------------------------------------
def listSubmissions(client, logfile):

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

    print(' ')
    print(' ')
    print('Listing all submissions for most recent HITs:')
    print('-----------------------------------------------')
    print(' ')

    total_assignment_count = 0

    # --------------------------------------------------------------------------------
    # iterate through each hit
    # --------------------------------------------------------------------------------
    for r, item in enumerate(retrieved_HITs):

        print('response', r)
        print('HIT Id:', item['HITId'])

        # Get the status of the HIT
        hit = client.get_hit(HITId=item['HITId'])
        item['status'] = hit['HIT']['HITStatus']

        # --------------------------------------------------------------------------------
        # Get a list of the Assignments that have been submitted by Workers
        # --------------------------------------------------------------------------------
        assignmentsList = client.list_assignments_for_hit(HITId=item['HITId'], AssignmentStatuses=['Submitted'],MaxResults=10)

        assignments = assignmentsList['Assignments']
        item['assignments_submitted_count'] = len(assignments)

        print(' # assignments submitted: ', item['assignments_submitted_count'])

        answers = []

        # --------------------------------------------------------------------------------
        # evaluating each assignment
        # --------------------------------------------------------------------------------

        for a in assignments:
            print(' ... assignment status:', a['AssignmentStatus'])

            # Retrieve the answers submitted by the Worker from the XML; put them in a dict + print answers
            assignment_id = a['AssignmentId']
            answer_xmltodict = xmltodict.parse(a['Answer'])['QuestionFormAnswers']['Answer']
            answer_dict = {}
            print('  {')
            for qa in answer_xmltodict:
                answer_dict[qa['QuestionIdentifier']] = qa['FreeText']
                print('    \'%s\'  :  %s' % (qa['QuestionIdentifier'], qa['FreeText']))
            print('  }\n')
            total_assignment_count += 1
        print(' ')
    print('total # assignments submitted (for all HITs):', total_assignment_count)


# ---------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print the submissions for a group of HITs')
    parser.add_argument('--logfile', dest='logfile', default='', help='Print the info for the HITs in this logfile. If no file is specified, information for all existing HITs will be printed.')
    args = parser.parse_args()
    # parse config info (vars: region, profile, env, flask_url)
    with open("turk_config.txt", "r+") as config:
        for line in config: exec(line)

    # initiate connection to turk server
    client, preview_url = init(region, profile, env)

    # review HITs
    listSubmissions(client, args.logfile)
