# Setup Guide — GitHub Activity Streaming Pipeline

## Prerequisites

- AWS account with appropriate permissions
- Python 3.12+
- AWS CLI configured (`aws configure`)
- pip packages: `boto3`, `requests`

---

## Step 1 — Create Kinesis Data Stream

1. Go to **AWS Console → Kinesis → Data Streams → Create stream**
2. Set the following:
   - **Name**: `ghactivity-stream`
   - **Capacity mode**: Provisioned
   - **Shard count**: 1
3. Click **Create data stream**
4. Wait for status to show **Active**

> **What is a shard?** A shard is the base throughput unit of a Kinesis stream. Each shard supports 1 MB/sec input and 2 MB/sec output. Add more shards if your producer exceeds this limit.

---

## Step 2 — Create S3 Bucket

1. Go to **AWS Console → S3 → Create bucket**
2. Set the following:
   - **Name**: `gharchive-live-stream` (must be globally unique)
   - **Region**: `us-east-1`
3. Leave all other settings as default
4. Click **Create bucket**

---

## Step 3 — Create Lambda Function

1. Go to **AWS Console → Lambda → Create function**
2. Set the following:
   - **Name**: `ghactivity-stream-consumer`
   - **Runtime**: Python 3.12
   - **Architecture**: x86_64
3. Click **Create function**
4. Copy the code from `lambda/lambda_function.py` into the code editor
5. Update the `bucket` variable with your S3 bucket name
6. Click **Deploy**

---

## Step 4 — Configure Lambda IAM Role

Your Lambda function needs permissions to read from Kinesis and write to S3.

1. Go to **IAM Console → Roles → find your Lambda role** (auto-created in Step 3)
2. Click **Add permissions → Attach policies**
3. Attach the following policies:
   - `AWSLambdaKinesisExecutionRole` — allows reading from Kinesis
   - `AmazonS3FullAccess` — allows writing to S3 (scope down in production)

> **Production tip**: Instead of `AmazonS3FullAccess`, create a custom policy scoped to your specific bucket ARN only.

---

## Step 5 — Add Kinesis Trigger to Lambda

1. Open your Lambda function
2. Click **Add trigger**
3. Set the following:
   - **Source**: Kinesis
   - **Kinesis stream**: `ghactivity-stream`
   - **Batch size**: 100
   - **Starting position**: Latest
4. Click **Add**

---

## Step 6 — Run the Producer

### Option A — Stream from GH Archive (recommended)

```python
# Install dependencies
pip install boto3 requests

# Run the producer
python producer/producer_dynamic.py
```

The producer fetches data directly from `https://data.gharchive.org/` and streams it into Kinesis in real time.

### Option B — Stream from local files

```python
python producer/producer_local.py
```

Make sure your local `.json.gz` files follow the GH Archive format.

---

## Step 7 — Verify Data Flow

**Check Kinesis Data Viewer:**
```
Kinesis Console → ghactivity-stream → Data viewer
→ Shard: shardId-000000000000
→ Starting position: Latest
→ Get records
```

**Check Lambda CloudWatch Logs:**
```
Lambda → ghactivity-stream-consumer → Monitor → View CloudWatch logs
```

**Check S3 output:**
```bash
aws s3 ls s3://gharchive-live-stream/kinesis-output/ --recursive
```

Expected S3 structure:
```
kinesis-output/
  year=2015/
    month=01/
      day=04/
        49673923567410020115133051487648...json
        49673923567410020115133051487649...json
```

---

## Architecture Overview

```
GH Archive URL
      ↓
  Producer Script (Python)
  - requests.get(url, stream=True)
  - gzip decompress line by line
  - kinesis.put_record() per event
      ↓
  Kinesis Data Stream (1 shard)
  - PartitionKey = event type
  - Retention: 24 hours
      ↓
  Lambda Consumer (triggered automatically)
  - base64 decode Kinesis payload
  - extract year/month/day from created_at
  - s3.put_object() with partitioned key
      ↓
  S3 Data Lake (partitioned by date)
```

---

## Key Concepts Demonstrated

| Concept | Implementation |
|---|---|
| Real-time streaming | Kinesis Data Streams |
| Serverless compute | AWS Lambda trigger |
| Memory-efficient ingestion | Python `yield` generator |
| Partitioned data lake | S3 keys with `year=/month=/day=` |
| Base64 decoding | Kinesis payload handling |
| IAM least privilege | Scoped Lambda execution role |

---

## Cost Considerations

| Service | Free Tier | Beyond Free Tier |
|---|---|---|
| Kinesis | 1 shard/month free for 12 months | ~$0.015/shard/hr |
| Lambda | 1M requests/month free | ~$0.20/1M requests |
| S3 | 5GB free for 12 months | ~$0.023/GB |

> **Tip**: Delete the Kinesis stream when not in use to avoid shard-hour charges.

---

## Security Notes

- Never hardcode AWS credentials in code
- Use IAM roles for service-to-service authentication
- Store sensitive config in environment variables or AWS Secrets Manager
- Scope IAM policies to specific resources in production

---

## Troubleshooting

**Producer sends records but S3 is empty:**
- Check Lambda CloudWatch logs for errors
- Verify Lambda IAM role has S3 write permissions
- Check if `base64.b64decode(...).decode('utf-8')` is present

**ProvisionedThroughputExceededException:**
- Your producer is exceeding 1 MB/sec on the shard
- Add `time.sleep()` between records or increase shard count

**Lambda not triggering:**
- Verify Kinesis trigger is enabled on Lambda
- Check Lambda execution role has `AWSLambdaKinesisExecutionRole`
