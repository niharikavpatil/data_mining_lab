import pandas as pd
import hashlib

files = [f"C:/Users/ub02-glab-057/Desktop/data_2/notices/part-{i:03d}.csv" for i in range(8)]
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

rows = []

for _, r in df.iterrows():
    text = str(r["title"]) + " " + str(r["body"])
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()

    for band in range(32):
        bucket = hashlib.sha1((h + str(band)).encode("utf-8")).hexdigest()
        rows.append((band, bucket, r["notice_id"]))

out = pd.DataFrame(rows, columns=["band_id", "bucket_hash", "notice_id"])
out.to_csv("lsh_buckets.csv", index=False)

print("===== TASK D : RELATIONAL RETRIEVAL STRUCTURE =====")
print("Notices:", len(df))
print("Bands:", 32)
print("Rows per signature:", 8)
print("LSH bucket rows:", len(out))
print("Output: lsh_buckets.csv")
