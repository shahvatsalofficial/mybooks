# FLAWED S3 INGESTION CODE
resp = s3.get_object(Bucket="quant-market-history", Key=f"ticks/NVDA/{date}.parquet")
raw_data = resp["Body"].read() # Reads 52.4 GB into RAM!
return base64.b64encode(raw_data).decode("ascii")
