import json
import urllib.parse
from agent import graph

def lambda_handler(event, context):
    """
    AWS Lambda handler triggered by S3 events.
    Processes uploaded audio files and generates gothic stories.
    """
    print("Received event:", event)
    try:
        # Parse S3 event
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            s3_key = urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8')
            
            # Only process audio files
            if not s3_key.lower().endswith(('.m4a', '.mp3', '.wav', '.flac')):
                continue
                
            print(f"Processing: s3://{bucket_name}/{s3_key}")
            
            # Initialize workflow state
            input_state = {
                "bucket_name": bucket_name,
                "audio_s3_key": s3_key,
                "counter": 1,
                "stories": [],
                "output_s3_keys": []
            }
            
            # Execute workflow
            result_state = graph.invoke(input_state)
            
            print(f"Generated {len(result_state['stories'])} stories")
            print(f"Uploaded to: {result_state['output_s3_keys']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Stories generated successfully')
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }