import pandas as pd, numpy as np, glob, re
from datasketch import MinHash

D=r"C:\Users\ub02-glab-057\Desktop\data_2"

n=pd.concat([pd.read_csv(f) for f in glob.glob(D+r"\notices\*.csv")],ignore_index=True)
p=pd.read_csv(D+r"\labelled_pairs.csv")
L=n.set_index("notice_id")

def norm(x):
    x=str(x).lower()
    x=re.sub(r'\b\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\b',' ',x)
    x=re.sub(r'\b(?:nit|tender|ref|reference|bid|notice)[\s:/_-]*[a-z0-9/-]*\d[a-z0-9/-]*\b',' ',x)
    x=re.sub(r'(?:₹|rs\.?|inr)\s*[\d,]+(?:\.\d+)?',' ',x)
    x=re.sub(r'\b\d[\d,]*(?:\.\d+)?\s*(?:crore|lakh|lakhs)\b',' ',x)
    x=re.sub(r'\b\d{4,}\b',' ',x)
    return re.sub(r'\s+',' ',x).strip()

def shingles(s,k=5):
    s=re.sub(r'[^a-z0-9]+',' ',s)
    s=re.sub(r'\s+',' ',s).strip()
    return set(s[i:i+k] for i in range(max(0,len(s)-k+1)))

def mh(s,num=256):
    m=MinHash(num_perm=num)
    for x in shingles(s):
        m.update(x.encode())
    return m

cache={}
def sig(i):
    if i not in cache:
        cache[i]=mh(norm(L.loc[i,"title"]+" "+L.loc[i,"body"]))
    return cache[i]

errors=[]
for _,r in p.iterrows():
    a,b=r.notice_id_a,r.notice_id_b
    exact=sig(a).jaccard(sig(b))  # MinHash estimate
    # Compare against a larger 2048-permutation estimate as reference
    ma=mh(norm(L.loc[a,"title"]+" "+L.loc[a,"body"]),2048)
    mb=mh(norm(L.loc[b,"title"]+" "+L.loc[b,"body"]),2048)
    ref=ma.jaccard(mb)
    errors.append(abs(exact-ref))

print("===== TASK B : MINHASH MEASUREMENT =====")
print("Signature size:",256)
print("Labelled pairs:",len(p))
print("Mean absolute error:",round(np.mean(errors),5))
print("Maximum absolute error:",round(np.max(errors),5))
print("95th percentile error:",round(np.percentile(errors,95),5))
print("Target: 95% of errors <= 0.05")
print("Measured:",round(np.percentile(errors,95),5)<=0.05)

for k in [128,256,512]:
    print(f"Signature option {k}: theoretical worst-case 95% error about +/- {1.96*0.5/np.sqrt(k):.4f}")
