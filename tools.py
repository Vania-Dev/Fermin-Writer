# tools.py - AWS-based utility functions for S3, Transcribe, and file operations
import boto3
import time
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')

def get_s3_audio_uri(bucket_name: str, s3_key: str) -> str:
    """
    Generate S3 URI for audio file (no download needed for Transcribe).
    
    Args:
        bucket_name: S3 bucket name
        s3_key: S3 object key
    
    Returns:
        S3 URI for the audio file
    """
    return f"s3://{bucket_name}/{s3_key}"

def transcribe_audio_with_aws(audio_s3_uri: str, job_name: str) -> str:
    """
    Transcribe audio using Amazon Transcribe service.
    
    Args:
        audio_s3_uri: S3 URI of the audio file (s3://bucket/key)
        job_name: Unique name for the transcription job
    
    Returns:
        Transcribed text content
    """
    try:
        print(f"Starting transcription job: {job_name}")
        
        # Start transcription job
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': audio_s3_uri},
            MediaFormat='m4a',
            LanguageCode='es-ES'  # Spanish
        )
        
        # Wait for job completion
        while True:
            response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                # Get transcript URI and download content
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                import requests
                transcript_response = requests.get(transcript_uri)
                transcript_data = transcript_response.json()
                
                # Extract text from transcript
                text = transcript_data['results']['transcripts'][0]['transcript']
                print("Transcription completed successfully")
                return text
                
            elif status == 'FAILED':
                return f"ERROR: Transcription failed: {response['TranscriptionJob'].get('FailureReason', 'Unknown error')}"
            
            print(f"Transcription status: {status}. Waiting...")
            time.sleep(10)
            
    except ClientError as e:
        return f"ERROR with AWS Transcribe: {e}"

def upload_text_to_s3(bucket_name: str, content: str, s3_key: str) -> str:
    """
    Upload text content directly to S3.
    
    Args:
        bucket_name: S3 bucket name
        content: Text content to upload
        s3_key: S3 object key (destination path)
    
    Returns:
        S3 URI of the uploaded file
    """
    try:
        print(f"Uploading text to S3: s3://{bucket_name}/{s3_key}")
        s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=content.encode('utf-8'))
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        print(f"Text uploaded to: {s3_uri}")
        return s3_uri
    except ClientError as e:
        return f"ERROR uploading to S3: {e}"


