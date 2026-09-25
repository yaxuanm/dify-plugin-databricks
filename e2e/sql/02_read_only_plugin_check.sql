-- Paste this single SELECT statement into the Databricks Query tool in Dify.
SELECT
  agreement_id,
  account_name,
  risk_flag,
  attainment_pct,
  compliance_pct,
  invoice_overdue_days,
  recommended_action
FROM demo_codex.contracts.contract_demo_account_snapshot
WHERE risk_flag IN ('high', 'medium')
ORDER BY
  CASE risk_flag
    WHEN 'high' THEN 1
    WHEN 'medium' THEN 2
    ELSE 3
  END,
  agreement_id
