import pandas as pd, re, glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

D=r"C:\Users\ub02-glab-057\Desktop\data_2"

n=pd.concat([pd.read_csv(f) for f in glob.glob(D+r"\notices\*.csv")],ignore_index=True)
p=pd.read_csv(D+r"\labelled_pairs.csv")

def norm(x):
    x=str(x).lower()
    x=re.sub(r'\b\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\b',' ',x)
    x=re.sub(r'\b(?:nit|tender|ref|reference|bid|notice)[\s:/_-]*[a-z0-9/-]*\d[a-z0-9/-]*\b',' ',x)
    x=re.sub(r'(?:₹|rs\.?|inr)\s*[\d,]+(?:\.\d+)?',' ',x)
    x=re.sub(r'\b\d[\d,]*(?:\.\d+)?\s*(?:crore|lakh|lakhs)\b',' ',x)
    x=re.sub(r'\b\d{4,}\b',' ',x)
    return re.sub(r'\s+',' ',x).strip()

n["raw"]=n.title.fillna('')+" "+n.body.fillna('')
n["norm"]=n.raw.map(norm)

lookup=n.set_index("notice_id")

def score(a,b,col,analyzer,ngram):
    v=TfidfVectorizer(analyzer=analyzer,ngram_range=(ngram,ngram))
    x=v.fit_transform([lookup.loc[a,col],lookup.loc[b,col]])
    return cosine_similarity(x[0],x[1])[0,0]

print("===== TASK A : SIMILARITY EVIDENCE =====")
print("Corpus notices:",len(n))
print("Labelled pairs:",len(p))
print("SAME:",(p.label=="same").sum())
print("DIFFERENT:",(p.label=="different").sum())

for a,b,label in [("N010018","N010020","SAME"),
                  ("N007876","N008565","DIFFERENT")]:
    print(f"\n{label}: {a} vs {b}")
    print("Word 3-gram raw:",round(score(a,b,"raw","word",3),4))
    print("Character 5-gram normalized:",round(score(a,b,"norm","char",5),4))

print("\nDECISION")
print("Representation: normalized character 5-grams")
print("Noise removed: dates, reference/tender numbers, monetary amounts, long numeric IDs")
print("Granularity: character 5-grams")
print("Reason: robust to wording changes, prefixes such as Corrigendum, and formatting differences")
print("Adoption cost: preprocessing + MinHash signature computation")
