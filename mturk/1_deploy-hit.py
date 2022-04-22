# deploy mturk HIT accepting voice recording from worker
# author: chris song

import boto3, urllib3
from init import init, yes_no
import argparse
import json
import os.path

# ---------------------------------------------------------------------------------------
# deploy HIT
# ---------------------------------------------------------------------------------------

def deployHITs(client, preview_url, start_index, end_index, logdir):

    logfile = os.path.join(logdir, 'launched_%d_%d.json' % (start_index, end_index))

    if os.path.exists(logfile):
        to_continue = yes_no('This set of HITs appears to have already been launched. Continue? (y/n)')
        if not to_continue:
            print('Aborting')
            return
        else:
            print('Launching HITs, existing logfile will be overwritten')
    # -------------------------------------------------------------------------------
    # HIT metadata
    # -------------------------------------------------------------------------------
    TaskAttributes = {
        'MaxAssignments': 1,                 
        'LifetimeInSeconds': 3*24*60*60,           
        'AssignmentDurationInSeconds': 60*10, 
        'Reward': '0.15',                     
        'Title': 'Record yourself describing some images out loud',
        'Keywords': 'sound, label, read, record, voice',
        'Description': 'Submit an audio recording of yourself describing 4 images.',
        'QualificationRequirements': [ # see https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mturk.html
            {
                'QualificationTypeId': '00000000000000000071',
                'Comparator': 'EqualTo',
                'LocaleValues': [{'Country': 'US'}],
                'RequiredToPreview': True,
                'ActionsGuarded':"DiscoverPreviewAndAccept"
            },
            {
                'QualificationTypeId': '000000000000000000L0',
                'Comparator': 'GreaterThan',
                'IntegerValues': [90],
                'RequiredToPreview': True,
                'ActionsGuarded':"DiscoverPreviewAndAccept"
            }
        ]
    }
    
    # -------------------------------------------------------------------------------
    # task prompts to be given in HITs
    # -------------------------------------------------------------------------------
    # general xml payload template
    # external task url is in here, with ${idx} in place of index
    question_xml =  """<ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
            <ExternalURL>${flask_url}/turk/${battery}/${idx}</ExternalURL>
            <FrameHeight>0</FrameHeight>
            </ExternalQuestion>"""

    for r in (("${flask_url}", flask_url), ("${battery}", battery)):
        question_xml = question_xml.replace(*r)

    # -------------------------------------------------------------------------------
    # HIT creations
    # -------------------------------------------------------------------------------
    hit_id_to_idx = {}
    hit_type_id = ''

    launched_hits = []

    num_launched = 0

    # loop through each sound
    for i in range(start_index,end_index+1):
        # prepare xml payload customized w/test idx
        question_enc = question_xml.replace('${idx}',str(i))

        # create hit using xml payload and task attributes
        hit = client.create_hit(**TaskAttributes,Question=question_enc)

        # save HIT type id for later
        hit_type_id = hit['HIT']['HITTypeId']

        # save hit_id-to-test-idx mappings
        hit_id_to_idx[hit['HIT']['HITId']] = i

        launched_hits.append(hit)

        num_launched += 1

        if num_launched % 20 == 0:
            print('Launched %d HITs...' % num_launched)

    print(' ')

    # print hit_id-to-sound mappings
    #for key,value in hit_id_to_idx.items():
    #    print("  %-30s %30s" % (key, value))

    print("You can view the HITs here:")
    print(preview_url + "?groupId={}".format(hit_type_id))
    print(' ')

    log_dict = {'attributes':TaskAttributes, 'hit_id_to_idx':hit_id_to_idx}

    with open(logfile, 'w') as fp:
        json.dump(log_dict, fp)

    print('HIT logfile saved at %s' % logfile)
# ---------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deploy a range of HITs')
    parser.add_argument('--logdir', dest='logdir', default='./hit_logs', help='Write the output log to this directory.')
    parser.add_argument('start_index', type=int)
    parser.add_argument('end_index', type=int)
    args = parser.parse_args()
    # parse config info (vars: region, profile, env, flask_url)
    with open("turk_config.txt", "r+") as config:
        for line in config: exec(line)

    # initiate connection to turk server
    client, preview_url = init(region, profile, env)

    # deploy HITs
    deployHITs(client, preview_url, args.start_index, args.end_index, args.logdir)
