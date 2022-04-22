# script to review + automatically accept/reject hits
# author: chris song

import boto3, xmltodict, json, os, csv
from init import init, yes_no
import argparse
from collections import OrderedDict
import json
import os.path
import sys

# ---------------------------------------------------------------------------------------
# retreive and print review of hits
# ---------------------------------------------------------------------------------------
def reviewHITs(client, logfile):

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
    print('Reviewing most recent HITs:')
    print('-----------------------------------------------')
    print(' ')

    total_ass_count = 0
    auto_accepted_ass_count = 0
    failed_ass_count = 0

    # --------------------------------------------------------------------------------
    # iterate through each hit
    # --------------------------------------------------------------------------------
    for r, item in enumerate(retrieved_HITs):

        print(' response', r)
        print(' HIT Id:', item['HITId'])

        # Get the status of the HIT
        hit = client.get_hit(HITId=item['HITId'])
        item['status'] = hit['HIT']['HITStatus']

        # --------------------------------------------------------------------------------
        # Get a list of the Assignments that have been submitted by Workers
        # --------------------------------------------------------------------------------
        assignmentsList = client.list_assignments_for_hit(HITId=item['HITId'], AssignmentStatuses=['Submitted', 'Approved'])

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
            if not isinstance(answer_xmltodict, list):
                failed_ass_count += 1
                total_ass_count += 1
                continue
            answer_dict = {}
            print('  answers for HIT:')
            print('  {')
            for qa in answer_xmltodict:
                answer_dict[qa['QuestionIdentifier']] = qa['FreeText']
                print('    \'%s\'  :  %s' % (qa['QuestionIdentifier'], qa['FreeText']))
            print('  }')

                # --------------------------------------------------------------------------------
            # approve the assignment, if worker passed all data validation stages. save assignment data into csv, json files
            # --------------------------------------------------------------------------------
            if a['AssignmentStatus'] == 'Submitted':
                file_dir = os.path.join(hits_save_location,answer_dict['environment'],'turk_data')
                os.makedirs(file_dir, exist_ok=True)

                # csv
                csv_path = os.path.join(file_dir,'worker_log.csv')
                if not os.path.exists(csv_path):
                    with open(csv_path, "w+") as f:
                        writer = csv.DictWriter(f,fieldnames=list(answer_dict.keys()))
                        writer.writeheader()
                        writer.writerow(answer_dict)
                else:
                    with open(csv_path, "a") as f:
                        writer = csv.DictWriter(f,fieldnames=list(answer_dict.keys()))
                        writer.writerow(answer_dict)

            # approve + dump to json
                if answer_dict['test_passed'] == 'True':
                    client.approve_assignment(AssignmentId=assignment_id,OverrideRejection=False)
                    os.makedirs(os.path.join(file_dir,'json','accepted'), exist_ok=True)
                    with open(os.path.join(file_dir,'json','accepted',assignment_id+'.json'), 'w+') as fp: json.dump(answer_dict, fp)
                    auto_accepted_ass_count += 1
                else:
                    os.makedirs(os.path.join(file_dir,'json','failed_auto_accept'), exist_ok=True)
                    with open(os.path.join(file_dir,'json','failed_auto_accept',assignment_id+'.json'), 'w+') as fp: json.dump(answer_dict, fp)
                    failed_ass_count += 1
            total_ass_count += 1
        print(' ')
    print('total # assignments evaluated:', total_ass_count)
    print('# assignments auto-approved:', auto_accepted_ass_count)
    print('# assignments failed auto-approve:', failed_ass_count)


# ---------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automatically review a group of HITs')
    parser.add_argument('--logfile', dest='logfile', default='', help='Review the HITs in this logfile. If no file is specified, review all existing HITs.')
    args = parser.parse_args()
    # parse config info (vars: region, profile, env, flask_url)
    with open("turk_config.txt", "r+") as config:
        for line in config: exec(line)

    # initiate connection to turk server
    client, preview_url = init(region, profile, env)

    # review HITs
    reviewHITs(client, args.logfile)
