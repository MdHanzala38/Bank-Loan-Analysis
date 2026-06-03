USE bank_loans;

-- ============================================================
-- SECTION 1: DATA CLEANING & SETUP
-- ============================================================

CREATE TABLE loans_clean AS SELECT * FROM loans_raw;

SET SESSION sql_mode = '';

ALTER TABLE loans_clean
    ADD COLUMN issue_date_parsed DATE,
    ADD COLUMN issue_year        SMALLINT,
    ADD COLUMN issue_month       TINYINT,
    ADD COLUMN issue_quarter     VARCHAR(7),
    ADD COLUMN issue_month_name  VARCHAR(3),
    ADD COLUMN int_rate_num      DECIMAL(5,2),
    ADD COLUMN term_months       TINYINT,
    ADD COLUMN emp_length_years  TINYINT,
    ADD COLUMN loan_category     VARCHAR(10);

DELETE t1 FROM loans_clean t1
INNER JOIN loans_clean t2
    ON t1.id = t2.id AND t1.id > t2.id;

UPDATE loans_clean
SET issue_date_parsed = STR_TO_DATE(CONCAT('01-', issue_d), '%d-%b-%Y');

UPDATE loans_clean
SET issue_year       = YEAR(issue_date_parsed),
    issue_month      = MONTH(issue_date_parsed),
    issue_quarter    = CONCAT(YEAR(issue_date_parsed), '-Q', QUARTER(issue_date_parsed)),
    issue_month_name = DATE_FORMAT(issue_date_parsed, '%b');

UPDATE loans_clean
SET int_rate_num = CAST(REPLACE(int_rate, '%', '') AS DECIMAL(5,2));

UPDATE loans_clean
SET term_months = CAST(REGEXP_REPLACE(term, '[^0-9]', '') AS UNSIGNED);

UPDATE loans_clean
SET emp_length_years = CASE emp_length
    WHEN '< 1 year'  THEN 0
    WHEN '1 year'    THEN 1
    WHEN '2 years'   THEN 2
    WHEN '3 years'   THEN 3
    WHEN '4 years'   THEN 4
    WHEN '5 years'   THEN 5
    WHEN '6 years'   THEN 6
    WHEN '7 years'   THEN 7
    WHEN '8 years'   THEN 8
    WHEN '9 years'   THEN 9
    WHEN '10+ years' THEN 10
    ELSE NULL
END;

UPDATE loans_clean
SET loan_category = CASE
    WHEN loan_status IN ('Fully Paid', 'Current') THEN 'Good'
    WHEN loan_status IN (
        'Charged Off', 'Default',
        'Late (31-120 days)', 'Late (16-30 days)',
        'In Grace Period') THEN 'Bad'
    ELSE 'Other'
END;

UPDATE loans_clean
SET annual_inc = (
    SELECT AVG(mid_val) FROM (
        SELECT annual_inc AS mid_val FROM loans_clean
        WHERE annual_inc IS NOT NULL
        ORDER BY annual_inc
        LIMIT 2 - (SELECT COUNT(*) FROM loans_clean WHERE annual_inc IS NOT NULL) % 2
        OFFSET (SELECT (COUNT(*) - 1) / 2 FROM loans_clean WHERE annual_inc IS NOT NULL)
    ) AS median_tbl
) WHERE annual_inc IS NULL;

UPDATE loans_clean SET emp_length = 'Unknown' WHERE emp_length IS NULL;
UPDATE loans_clean SET purpose    = 'Unknown' WHERE purpose    IS NULL;


-- ============================================================
-- SECTION 2: KPI QUERIES
-- ============================================================

SELECT
    COUNT(*)                                                        AS total_applications,
    COUNT(DISTINCT addr_state)                                      AS states_covered,
    MIN(issue_date_parsed)                                          AS first_loan_date,
    MAX(issue_date_parsed)                                          AS last_loan_date
FROM loans_clean;

SELECT
    COUNT(*)                                                        AS total_applications,
    SUM(CASE WHEN loan_category = 'Good' THEN 1 ELSE 0 END)        AS good_loan_count,
    SUM(CASE WHEN loan_category = 'Bad'  THEN 1 ELSE 0 END)        AS bad_loan_count,
    ROUND(SUM(CASE WHEN loan_category = 'Good' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS good_loan_pct,
    ROUND(SUM(CASE WHEN loan_category = 'Bad'  THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_loan_pct,
    ROUND(SUM(funded_amnt)  / 1e6, 2)                              AS total_funded_M,
    ROUND(SUM(total_pymnt)  / 1e6, 2)                              AS total_received_M,
    ROUND((SUM(total_pymnt) - SUM(funded_amnt)) / 1e6, 2)          AS net_M,
    ROUND(SUM(total_pymnt) * 100.0 / NULLIF(SUM(funded_amnt),0),2) AS collection_rate_pct,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate,
    ROUND(AVG(dti), 2)                                              AS avg_dti,
    ROUND(AVG(funded_amnt), 2)                                      AS avg_loan_amount,
    ROUND(AVG(annual_inc), 2)                                       AS avg_annual_income
FROM loans_clean;

SELECT
    COUNT(*)                                                        AS good_loan_applications,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM loans_clean),2) AS good_loan_pct,
    ROUND(SUM(funded_amnt), 2)                                      AS good_loan_funded,
    ROUND(SUM(total_pymnt), 2)                                      AS good_loan_received
FROM loans_clean
WHERE loan_category = 'Good';

SELECT
    COUNT(*)                                                        AS bad_loan_applications,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM loans_clean),2) AS bad_loan_pct,
    ROUND(SUM(funded_amnt), 2)                                      AS bad_loan_funded,
    ROUND(SUM(total_pymnt), 2)                                      AS bad_loan_received,
    ROUND(SUM(funded_amnt) - SUM(total_pymnt), 2)                   AS bad_loan_loss
FROM loans_clean
WHERE loan_category = 'Bad';

SELECT
    loan_status,
    loan_category,
    COUNT(*)                                                        AS applications,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)             AS pct_of_total,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M,
    ROUND(SUM(total_pymnt) / 1e6, 2)                               AS received_M,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate,
    ROUND(AVG(dti), 2)                                              AS avg_dti
FROM loans_clean
GROUP BY loan_status, loan_category
ORDER BY applications DESC;

SELECT
    issue_year,
    issue_month,
    issue_month_name,
    COUNT(*)                                                        AS applications,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M,
    ROUND(SUM(total_pymnt) / 1e6, 2)                               AS received_M,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate,
    ROUND(AVG(dti), 2)                                              AS avg_dti,
    LAG(COUNT(*)) OVER (ORDER BY issue_year, issue_month)           AS prev_month_apps,
    ROUND((COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY issue_year, issue_month))
        * 100.0 / NULLIF(LAG(COUNT(*)) OVER (ORDER BY issue_year, issue_month),0),2)
                                                                    AS mom_change_pct
FROM loans_clean
GROUP BY issue_year, issue_month, issue_month_name
ORDER BY issue_year, issue_month;

SELECT
    issue_year,
    COUNT(*)                                                        AS total_applications,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M,
    ROUND(SUM(total_pymnt) / 1e6, 2)                               AS received_M,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate,
    ROUND(AVG(dti), 2)                                              AS avg_dti,
    ROUND(SUM(CASE WHEN loan_category = 'Good' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS good_loan_pct,
    ROUND(SUM(CASE WHEN loan_category = 'Bad'  THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_loan_pct
FROM loans_clean
GROUP BY issue_year
ORDER BY issue_year;


-- ============================================================
-- SECTION 3: CUSTOMER SEGMENT QUERIES
-- ============================================================

SELECT
    grade,
    COUNT(*)                                                        AS total_loans,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)             AS share_pct,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate,
    ROUND(AVG(loan_amnt), 2)                                        AS avg_loan_amount,
    ROUND(AVG(annual_inc), 2)                                       AS avg_income,
    ROUND(AVG(dti), 2)                                              AS avg_dti,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M
FROM loans_clean
GROUP BY grade
ORDER BY grade;

SELECT
    purpose,
    COUNT(*)                                                        AS total_loans,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)             AS share_pct,
    ROUND(AVG(loan_amnt), 2)                                        AS avg_loan_amount,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate,
    ROUND(AVG(dti), 2)                                              AS avg_dti,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M
FROM loans_clean
GROUP BY purpose
ORDER BY total_loans DESC;

SELECT
    home_ownership,
    COUNT(*)                                                        AS total_loans,
    ROUND(AVG(loan_amnt), 2)                                        AS avg_loan_amount,
    ROUND(AVG(annual_inc), 2)                                       AS avg_income,
    ROUND(AVG(dti), 2)                                              AS avg_dti,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M
FROM loans_clean
GROUP BY home_ownership
ORDER BY total_loans DESC;

SELECT
    emp_length,
    emp_length_years,
    COUNT(*)                                                        AS total_loans,
    ROUND(AVG(loan_amnt), 2)                                        AS avg_loan_amount,
    ROUND(AVG(annual_inc), 2)                                       AS avg_income,
    ROUND(AVG(dti), 2)                                              AS avg_dti,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct
FROM loans_clean
GROUP BY emp_length, emp_length_years
ORDER BY emp_length_years ASC;

SELECT
    term,
    term_months,
    COUNT(*)                                                        AS total_loans,
    ROUND(AVG(loan_amnt), 2)                                        AS avg_loan_amount,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate,
    ROUND(AVG(dti), 2)                                              AS avg_dti,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M
FROM loans_clean
GROUP BY term, term_months
ORDER BY term_months;

SELECT
    verification_status,
    COUNT(*)                                                        AS total_loans,
    ROUND(AVG(annual_inc), 2)                                       AS avg_income,
    ROUND(AVG(dti), 2)                                              AS avg_dti,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M
FROM loans_clean
GROUP BY verification_status
ORDER BY bad_rate_pct DESC;

SELECT
    addr_state                                                      AS state,
    COUNT(*)                                                        AS total_loans,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate,
    ROUND(AVG(annual_inc), 2)                                       AS avg_income,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M
FROM loans_clean
GROUP BY addr_state
ORDER BY total_loans DESC
LIMIT 15;

SELECT
    CASE
        WHEN annual_inc < 40000                  THEN '< $40K'
        WHEN annual_inc BETWEEN 40000  AND 79999  THEN '$40K-$80K'
        WHEN annual_inc BETWEEN 80000  AND 119999 THEN '$80K-$120K'
        WHEN annual_inc BETWEEN 120000 AND 199999 THEN '$120K-$200K'
        ELSE '$200K+'
    END                                                             AS income_bucket,
    COUNT(*)                                                        AS total_loans,
    ROUND(AVG(loan_amnt), 2)                                        AS avg_loan_amount,
    ROUND(AVG(dti), 2)                                              AS avg_dti,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M
FROM loans_clean
GROUP BY income_bucket
ORDER BY MIN(annual_inc);

SELECT
    CASE
        WHEN dti < 10              THEN '0-10 Low'
        WHEN dti BETWEEN 10 AND 19 THEN '10-20 Moderate'
        WHEN dti BETWEEN 20 AND 29 THEN '20-30 High'
        WHEN dti BETWEEN 30 AND 39 THEN '30-40 Very High'
        ELSE '40+ Critical'
    END                                                             AS dti_bucket,
    COUNT(*)                                                        AS total_loans,
    ROUND(AVG(annual_inc), 2)                                       AS avg_income,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct
FROM loans_clean
GROUP BY dti_bucket
ORDER BY MIN(dti);

SELECT
    grade,
    purpose,
    COUNT(*)                                                        AS total_loans,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct
FROM loans_clean
GROUP BY grade, purpose
HAVING COUNT(*) > 100
ORDER BY bad_rate_pct DESC
LIMIT 20;

SELECT
    issue_year,
    grade,
    COUNT(*)                                                        AS total_loans,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct
FROM loans_clean
GROUP BY issue_year, grade
ORDER BY issue_year, grade;

SELECT
    COUNT(*)                                                        AS high_risk_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM loans_clean),2) AS pct_of_portfolio,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct
FROM loans_clean
WHERE grade          IN ('E', 'F', 'G')
  AND dti            > 30
  AND term_months    = 60
  AND home_ownership = 'RENT';

SELECT
    COUNT(*)                                                        AS low_risk_count,
    ROUND(SUM(funded_amnt) / 1e6, 2)                               AS funded_M,
    ROUND(SUM(CASE WHEN loan_category = 'Bad' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                    AS bad_rate_pct,
    ROUND(AVG(int_rate_num), 2)                                     AS avg_int_rate
FROM loans_clean
WHERE grade              IN ('A', 'B')
  AND dti                < 15
  AND emp_length_years   >= 5
  AND home_ownership     IN ('OWN', 'MORTGAGE');
