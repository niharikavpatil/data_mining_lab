import csv, re, math
from collections import defaultdict

DATA = r"C:\Users\ub02-glab-057\Desktop\data_2"
NOTICE_DIR = DATA + r"\notices"
LABELS = DATA + r"\labelled_pairs.csv"

# ---------- Load notices ----------
notices = {}

import glob
for fn in glob.glob(NOTICE_DIR + r"\*.csv"):
    with open(fn, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            notices[row["notice_id"]] = row

# ---------- Normalization ----------
def raw_text(n):
    return (n["title"] + " " + n["body"]).lower()

def normalize_text(n):
    s = raw_text(n)

    # Remove dates such as 2025-05-27, 27/05/2025, 27-05-2025
    s = re.sub(r"\b\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\b", " ", s)

    # Remove tender/reference numbers containing letters + digits
    s = re.sub(r"\b(?:nit|nitno|tender|ref|reference|bid|notice)[\s:/_-]*[a-z0-9/-]*\d[a-z0-9/-]*\b", " ", s)

    # Remove monetary amounts and currency forms
    s = re.sub(r"(?:₹|rs\.?|inr)\s*[\d,]+(?:\.\d+)?", " ", s)
    s = re.sub(r"\b\d[\d,]*(?:\.\d+)?\s*(?:crore|lakh|lakhs)\b", " ", s)

    # Remove standalone long numeric strings
    s = re.sub(r"\b\d{4,}\b", " ", s)

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def word_shingles(s, k=3):
    words = re.findall(r"[a-z0-9]+", s)
    return set(" ".join(words[i:i+k]) for i in range(len(words)-k+1))

def char_shingles(s, k=5):
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return set(s[i:i+k] for i in range(len(s)-k+1))

def jaccard(a,b):
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)

# ---------- Labelled pairs ----------
pairs = []
with open(LABELS, "r", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        pairs.append(r)

def score_pair(a,b,kind):
    if kind == "word3":
        return jaccard(word_shingles(raw_text(a),3), word_shingles(raw_text(b),3))
    else:
        return jaccard(char_shingles(normalize_text(a),5),
                       char_shingles(normalize_text(b),5))

results = []

for p in pairs:
    a = notices[p["notice_id_a"]]
    b = notices[p["notice_id_b"]]
    results.append({
        "label": p["label"],
        "word3": score_pair(a,b,"word3"),
        "char5norm": score_pair(a,b,"char5norm")
    })

for label in ["same","different"]:
    subset = [r for r in results if r["label"] == label]
    print(f"\n{label.upper()} PAIRS: {len(subset)}")
    for key in ["word3","char5norm"]:
        vals = [r[key] for r in subset]
        print(f"  {key}: mean={sum(vals)/len(vals):.4f}, "
              f"min={min(vals):.4f}, max={max(vals):.4f}")

print("\nSELECTED EXAMPLES")
examples = [
    ("N010018","N010020","SAME"),
    ("N007876","N008565","DIFFERENT")
]

for a_id,b_id,label in examples:
    a,b = notices[a_id],notices[b_id]
    print(f"\n{label}: {a_id} vs {b_id}")
    print("  title A:", a["title"])
    print("  title B:", b["title"])
    print(f"  word3 raw Jaccard   = {score_pair(a,b,'word3'):.4f}")
    print(f"  char5 normalized Jaccard = {score_pair(a,b,'char5norm'):.4f}")

# ---------- Simple threshold sweep ----------
print("\nTHRESHOLD COMPARISON")

for key in ["word3","char5norm"]:
    print(f"\n{key}")
    for threshold in [0.20,0.30,0.40,0.50,0.60,0.70,0.80]:
        tp = sum(r[key] >= threshold and r["label"]=="same" for r in results)
        fn = sum(r[key] < threshold and r["label"]=="same" for r in results)
        fp = sum(r[key] >= threshold and r["label"]=="different" for r in results)
        tn = sum(r[key] < threshold and r["label"]=="different" for r in results)

        recall = tp/(tp+fn) if tp+fn else 0
        fpr = fp/(fp+tn) if fp+tn else 0

        print(f"  threshold={threshold:.2f}  same_recall={recall:.3f}  "
              f"different_FPR={fpr:.3f}")
