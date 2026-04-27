import json
import boto3
import base64

s3=boto3.client('s3')
bucket=BUCKET_NAME   #env var

def lambda_handler(event, context):
    
    for record in event['Records']:
        
        # Kinesis data is base64 encoded so decode here
        payload=base64.b64decode(record['kinesis']['data']).decode('utf-8')

        event_data=json.loads(payload)
        event_id=event_data.get('id', 'unknown')
        
        # Upload to S3
        created_at=event_data.get('created_at', 'unknown')
        year=created_at[0:4]
        month=created_at[5:7]
        day=created_at[8:10]
        batch_id=record['kinesis']['sequenceNumber']

        s3.put_object(Bucket=bucket, Key=f"kinesis-output/year={year}/month={month}/day={day}/{batch_id}.json", Body=json.dumps(event_data))
        
    return 'Successfully processed {} records.'.format(len(event['Records']))
