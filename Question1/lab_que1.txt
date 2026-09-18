-- Annappura Stores Data Mining Lab 1

-- Task A: Partitioned object-store layout
-- sales/store=S01/year=2024/month=10/*.csv
-- 4,457 total files organized into 144 store-month partitions.
-- S01 October: 31 files, 846,899 bytes.
-- Original dataset: 4,457 files, 68,706,877 bytes.
-- File reduction: 99.30%
-- Byte reduction: 98.77%

-- Task B: Canonical deduplication
CREATE OR REPLACE TABLE canonical_sales (
    bill_no VARCHAR NOT NULL,
    line_no BIGINT NOT NULL,
    product_code VARCHAR,
    qty BIGINT,
    unit_price DOUBLE,
    line_type VARCHAR,
    ts TIMESTAMP,
    source_file VARCHAR,
    PRIMARY KEY (bill_no, line_no)
);

-- Task C: Fact table
CREATE OR REPLACE TABLE fact_sales AS
SELECT
    bill_no,
    line_no,
    product_code,
    strptime(
        regexp_extract(source_file, 'SALES_[^_]+_([0-9]{8})', 1),
        '%Y%m%d'
    )::DATE AS business_date,
    qty,
    unit_price,
    line_type,
    CASE
        WHEN line_type = 'SALE' THEN qty * unit_price
        WHEN line_type IN ('RETURN','DISCOUNT','VOID')
            THEN -ABS(qty * unit_price)
        ELSE 0
    END AS revenue,
    source_file
FROM canonical_sales;

-- Task D: Historical March prices
SELECT
    f.product_code,
    f.business_date,
    p.product_sk,
    p.product_name,
    pr.selling_price AS march_price
FROM fact_sales f
JOIN pg.public.products p
  ON f.product_code = p.product_code
 AND f.business_date >= p.valid_from
 AND (p.valid_to IS NULL OR f.business_date < p.valid_to)
JOIN pg.public.price_revisions pr
  ON p.product_sk = pr.product_sk
 AND f.business_date >= pr.effective_from
 AND (pr.effective_to IS NULL OR f.business_date < pr.effective_to)
WHERE f.business_date >= DATE '2024-03-01'
  AND f.business_date < DATE '2024-04-01';

-- Task E: Cross-system query
SELECT
    f.business_date,
    s.store_name,
    c.category_name,
    ROUND(SUM(f.revenue),2) AS revenue
FROM fact_sales f
JOIN pg.public.stores s
  ON regexp_extract(f.bill_no, '^(S[0-9]+)', 1) = s.store_id
JOIN pg.public.products p
  ON f.product_code = p.product_code
 AND f.business_date >= p.valid_from
 AND (p.valid_to IS NULL OR f.business_date < p.valid_to)
JOIN pg.public.product_categories c
  ON p.category_id = c.category_id
GROUP BY 1,2,3;

-- Task F: October reconciliation
SELECT
    ROUND(SUM(revenue),2) AS calculated_october,
    56359195.92 AS finance_october,
    ROUND(56359195.92 - SUM(revenue),2) AS difference
FROM fact_sales
WHERE business_date >= DATE '2024-10-01'
  AND business_date < DATE '2024-11-01';

-- Result:
-- Calculated: ₹56,348,009.24
-- Finance:    ₹56,359,195.92
-- Difference: ₹11,186.68