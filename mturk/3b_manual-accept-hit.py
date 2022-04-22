# script to review + automatically accept/reject hits
# author: chris song

import boto3, xmltodict, json, os
from init import init
import argparse
import json
import os.path

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
	print('Reviewing most recent (up to 10) HITs:')
	print('-----------------------------------------------')
	print(' ')

	total_assignment_count = 0
	accepted_assignment_count = 0
	rejected_assignment_count = 0

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
			print('  answers for HIT:')
			print('  {')
			for qa in answer_xmltodict:
				answer_dict[qa['QuestionIdentifier']] = qa['FreeText']
				print('    \'%s\'  :  %s' % (qa['QuestionIdentifier'], qa['FreeText']))
			print('  }')

	        	# --------------------------------------------------------------------------------
			# approve the assignment, if worker passed all data validation stages. save as json
			# --------------------------------------------------------------------------------
			if a['AssignmentStatus'] == 'Submitted':
				print("  accept this HIT? '1' = accept, '2' = reject, '3' = decide later")
				choice = input().lower()
				if choice == '1':
					client.approve_assignment(AssignmentId=assignment_id,OverrideRejection=False)
					with open('hits/accepted/'+assignment_id+'.json', 'w+') as fp: json.dump(answer_dict, fp)
					accepted_assignment_count += 1
					if os.path.isfile('hits/failed_auto_accept/'+assignment_id+'.json'): os.remove('hits/failed_auto_accept/'+assignment_id+'.json')
					print('  accepted.')
				elif choice == '2':
					print("    message to worker:")
					message = input()
					print('')
					client.reject_assignment(AssignmentId=assignment_id,RequesterFeedback=message)
					with open('hits/rejected/'+assignment_id+'.json', 'w+') as fp: json.dump(answer_dict, fp)
					rejected_assignment_count += 1
					if os.path.isfile('hits/failed_auto_accept/'+assignment_id+'.json'): os.remove('hits/failed_auto_accept/'+assignment_id+'.json')
					print('  rejected. message sent.')
				elif choice == '3':
					print('  deciding later.')
				else:
					sys.stdout.write("Please respond with '1', '2', or '3'")
			total_assignment_count += 1
		print(' ')
	print('total # assignments evaluated:', total_assignment_count)
	print('      # assignments manually approved:', accepted_assignment_count)
	print('      # assignments manually rejected:', rejected_assignment_count)


# ---------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Manually review a group of HITs')
    parser.add_argument('--logfile', dest='logfile', default='', help='Review the HITs in this logfile. If no file is specified, review all existing HITs.')
    args = parser.parse_args()
	# parse config info (vars: region, profile, env, flask_url)
	with open("turk_config.txt", "r+") as config:
		for line in config: exec(line)

	# initiate connection to turk server
	client, preview_url = init(region, profile, env)

	# review HITs
	reviewHITs(client, args.logfile)