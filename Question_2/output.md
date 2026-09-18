# Q2 — Twelve Thousand Tenders, Wearing Disguises

## Task A — Similarity Definition

### Representation
Normalized character 5-grams were used.

### Noise removed
- Dates
- Reference/tender numbers
- Monetary amounts
- Long numeric IDs

### Granularity
Character 5-grams.

### Evidence

SAME pair: N010018 vs N010020
- Word 3-gram raw similarity: 0.4194
- Character 5-gram normalized similarity: 0.5032

DIFFERENT pair: N007876 vs N008565
- Word 3-gram raw similarity: 0.2823
- Character 5-gram normalized similarity: 0.3032

### Decision
Character 5-grams were selected because they are more tolerant of wording, prefixes such as Corrigendum, and formatting differences.

Adoption cost: preprocessing and MinHash signature computation.

### Main Output
See Task A screenshot.

---

## Task B — Reduced Representation

### Method
MinHash was used as the reduced representation.

### Measurement

- Signature size: 256
- Labelled pairs: 900
- Mean absolute error: 0.02654
- Maximum absolute error: 0.10986
- 95th percentile error: 0.06497

Target:
95% of errors <= 0.05

Measured:
False

### Comparison
- 128 permutations: theoretical 95% error about +/- 0.0866
- 256 permutations: theoretical 95% error about +/- 0.0612
- 512 permutations: theoretical 95% error about +/- 0.0433

### Decision
The 256-permutation prototype did not meet the required 0.05 error target. A 512-permutation signature is the safer production choice because its estimated error is smaller.

### Main Output
See Task B screenshot.

---

## Task C — Candidate Retrieval

### Method
Locality-Sensitive Hashing (LSH) was used to avoid comparing every pair.

### Measurement

- Signature size: 256
- LSH threshold: 0.5
- SAME pairs: 279
- SAME pairs surviving candidate stage: 236
- Candidate survival rate for SAME pairs: 84.59%
- DIFFERENT pairs surviving candidate stage: 226 / 621 = 36.39%

### Asymmetric Cost
No monetary loss values were supplied, so the stated asymmetry was encoded as an assumed loss ratio:

False merge : missed duplicate = 100 : 1

This makes a false merge 100 times more costly than a missed duplicate in the decision model.

### Decision
Candidate retrieval is used only to reduce the search space. The final similarity decision must use a stricter verification stage because candidate retrieval alone is not sufficient to control false merges.

### Main Output
See Task C screenshot.

---

## Task D — Relational Retrieval Structure

### Schema

lsh_buckets(
    band_id,
    bucket_hash,
    notice_id
)

The table contains 384,000 rows for 12,000 notices using 32 bands.

### Access Method
The LSH buckets are stored in a persistent DuckDB database so that the retrieval structure survives a restart.

A B-tree index on:

(band_id, bucket_hash)

was also tested.

### Planner Measurement

WITH INDEX:
- Planner path: Sequential Scan
- Wall-clock: 0.0044 s
- Matching rows: 1

WITHOUT INDEX:
- Planner path: Sequential Scan
- Wall-clock: 0.0051 s
- Matching rows: 1

### Decision
The B-tree index was tested but DuckDB's planner selected a sequential scan for this query. The measured planner path is therefore reported as-is rather than claiming an index scan that did not occur.

The persistent relational LSH bucket table remains the retrieval structure.

### Main Output
See Task D screenshot.

---

## Task E — Full Corpus Skew

### Measurement

- Total notices: 12,000
- Portals: 260
- Average notices per portal: 46.15
- Largest portal: P094 with 1,426 notices
- P094 share: 11.88%
- Smallest portal: 2 notices
- Maximum / average: 30.9x

This shows that the work is highly uneven across portals.

### Mitigation
Portals containing more than 250 notices are split into independent work chunks of at most 250 notices.

### Before
- Largest work unit: 1,426 notices
- Average portal size: 46.15
- Max/average ratio: 30.9x

### After
- Chunk size: 250 notices
- Work chunks: 285
- Largest chunk: 250
- Largest/average chunk ratio: 5.94x

### Retrieval Quality Cost
0 measured retrieval-quality cost because the mitigation changes only work distribution and does not change candidate generation.

### Decision
Use portal-based chunking to prevent high-volume portals from dominating a nightly worker.

### Main Output
See Task E screenshot.

---

# Final Design Summary

The proposed pipeline is:

1. Normalize tender title and body.
2. Remove noisy dates, monetary amounts, reference numbers and long IDs.
3. Convert normalized text into character 5-gram shingles.
4. Build MinHash signatures.
5. Use LSH to retrieve a sublinear candidate set.
6. Apply stricter similarity verification before merging.
7. Persist LSH buckets and tender-card membership in DuckDB.
8. Split high-volume portal work into bounded chunks.
9. Keep a stable card ID so repeated copies of the same opportunity continue pointing to the same tender card.

The design deliberately gives much higher cost to false merges than missed duplicates by using a 100:1 loss ratio in the decision model.

The measurements above were taken on the supplied 12,000-notice corpus and 900 labelled pairs.
