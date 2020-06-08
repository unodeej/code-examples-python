import boto3

s3 = boto3.resource('s3')

for bucket in s3.buckets.all():
    print(bucket.name)

data = open('requirements.txt', 'rb')
s3.Bucket('enrollhero-test').put_object(Key='AARPTESTDOC.txt', Body=data)
