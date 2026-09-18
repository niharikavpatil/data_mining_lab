import pandas as pd, numpy as np, glob, re
from datasketch import MinHash, MinHashLSH

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

def make_mh(s):
    m=MinHash(num_perm=256)
    s=re.sub(r'[^a-z0-9]+',' ',s)
    s=re.sub(r'\s+',' ',s).strip()
    for i in range(max(0,len(s)-4)):
        m.update(s[i:i+5].encode())
    return m

print("Building LSH index...")
lsh=MinHashLSH(threshold=0.50,num_perm=256)

for _,r in n.iterrows():
    lsh.insert(r.notice_id,make_mh(norm(r.title+" "+r.body)))

print("===== TASK C : LSH CANDIDATE MEASUREMENT =====")
print("LSH threshold:",0.50)
print("Signature size:",256)

for label in ["same","different"]:
    rows=p[p.label==label]
    survived=0
    for _,r in rows.iterrows():
        a=make_mh(norm(L.loc[r.notice_id_a,"title"]+" "+L.loc[r.notice_id_a,"body"]))
        if r.notice_id_b in lsh.query(a):
            survived+=1
    print(label.upper(),"pairs:",len(rows),"survived:",survived,
          "rate:",round(survived/len(rows),4))

print("\nCOST RATIO")
print("False merge : missed duplicate = 100 : 1")
print("Operating principle: favor high candidate recall; final similarity threshold handles false merges.")
