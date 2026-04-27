#Github Activity Real-Time Streaming Pipeline

##Tech Stack
-AWS Kinesis Data Streams
-AWS Lambda
-Amazon S3
-Python (boto3, requests)

##What it does
1. Producer fetches live Github events from GH Archive
2. Streams records into Kinesis Data Streams
3. Lamba consumes records and writes to s3 (partitioned by year/month/day)

##Key Concepts Demonstrated
-Real-Time event Streaming
-Serverless compute (Lambda)
-Partitioned data lake on S3
-Base64 decodfing of Kinesis records
-Generator pattern for memory-efficient Streaming


