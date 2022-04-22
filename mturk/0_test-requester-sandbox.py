import boto3

region = 'us-east-1'

# endpoint of developer environment 
endpoint_url = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com' # sandbox
#endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com' # production

# read AWS access keys from ~/.aws/credentials
session = boto3.Session(profile_name = 'mturk-csong23')

# initiate connection to service
client = session.client(
    service_name='mturk',
    endpoint_url=endpoint_url,
    region_name=region,
)

# Should return $10,000.00 in the MTurk Developer Sandbox
print(client.get_account_balance()['AvailableBalance'])