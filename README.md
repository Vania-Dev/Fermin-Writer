# Fermin Writer - AWS Edition

A gothic story generator that processes audio files using AWS services to create haunting narratives in the style of Fermín Romero de Torres from "The Shadow of the Wind".

## AWS Services Used

- **Amazon S3**: Storage for audio files and generated stories
- **Amazon Transcribe**: Audio-to-text transcription
- **Amazon Bedrock**: AI-powered story generation using Amazon Nova

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS credentials:**
   - Copy `.env.example` to `.env`
   - Fill in your AWS credentials and S3 bucket information
   - Or use AWS CLI: `aws configure`

3. **Create S3 bucket and upload audio:**
   ```bash
   aws s3 mb s3://your-fermin-bucket
   aws s3 cp audio/audio.m4a s3://your-fermin-bucket/audio/
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Configuration

Set these environment variables in `.env`:

- `S3_BUCKET_NAME`: Your S3 bucket name
- `AUDIO_S3_KEY`: Path to audio file in S3 (e.g., "audio/audio.m4a")
- `AWS_DEFAULT_REGION`: AWS region (default: us-east-1)

## Workflow

1. **Download**: Fetches audio file from S3
2. **Transcribe**: Uses Amazon Transcribe to convert audio to text
3. **Generate**: Creates 3 gothic story variations using Bedrock
4. **Upload**: Saves generated stories back to S3

## Output

Generated stories are uploaded to S3 under the `fermin-audio/history/` prefix:
- `fermin-audio/history/{audio_name}_story_1.txt`
- `fermin-audio/history/{audio_name}_story_2.txt`
- `fermin-audio/history/{audio_name}_story_3.txt`

## AWS Permissions

Bucket S3

- `s3:GetObject`
- `s3:PutObject`
- `s3:ListBucket`

AWS Lambda
- `s3:GetObject`
- `s3:PutObject`
- `s3:ListBucket`
- `bedrock:InvokeModel`
- `transcribe:StartTranscriptionJob`
- `transcribe:GetTranscriptionJob`
- `transcribe:ListTranscriptionJobs`