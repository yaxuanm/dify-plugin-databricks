-- Run once in a non-production Databricks SQL editor, not through the Dify tool.
-- The statements create only synthetic demonstration data.
CREATE CATALOG IF NOT EXISTS demo_codex;
CREATE SCHEMA IF NOT EXISTS demo_codex.contracts;

CREATE OR REPLACE TABLE demo_codex.contracts.contract_demo_account_snapshot (
  agreement_id STRING,
  account_type STRING,
  account_name STRING,
  counterparty_name STRING,
  region STRING,
  contract_status STRING,
  period_label STRING,
  metric_basis STRING,
  target_value DOUBLE,
  actual_value DOUBLE,
  attainment_pct DOUBLE,
  compliance_pct DOUBLE,
  invoice_overdue_days INT,
  security_incidents_30d INT,
  customer_satisfaction DOUBLE,
  projected_rebate_usd DOUBLE,
  rebate_cap_usd DOUBLE,
  next_renewal_date DATE,
  risk_flag STRING,
  recommended_action STRING
);

INSERT OVERWRITE demo_codex.contracts.contract_demo_account_snapshot VALUES
('SAA-2026-EMEA-118','enterprise_partner','Crestline Enterprise Solutions GmbH','Helio Data Infrastructure Ltd.','EMEA - DACH and Benelux','active','FY2026 YTD','revenue_commitment_eur',3000000,2415000,80.5,100,0,1,54,NULL,NULL,DATE'2027-05-15','medium','Prepare remediation plan and review whether alliance benefits should be reduced if annual attainment stays below 85 percent'),
('PCA-2026-NE-041','enterprise_partner','BluePeak Advisory Partners LLC','Northstar Commerce Systems Inc.','US and Canada - Northeast','active','FY2026 YTD','booking_commitment_usd',2500000,1980000,79.2,100,0,0,4.3,NULL,NULL,DATE'2027-04-01','high','Assess whether exclusivity should convert to non-exclusive because bookings are more than 15 percent below target and satisfaction is below threshold'),
('RBT-2026-001-A','rebate_customer','ClearView Optical Group LLC','Orion Vision Technologies Inc.','US West','active','FY2026 YTD','annual_net_purchases_usd',50000,342000,114.0,100,0,0,NULL,30780,120000,DATE'2027-02-01','low','Customer qualifies for the 9 percent tier; confirm approved lab sourcing and monthly reporting are current'),
('RBT-2026-002-B','rebate_customer','Summit Health Clinics Inc.','NovaMed Supply Co.','Mountain Region','active','Q2 FY2026','quarterly_net_spend_usd',200000,228500,114.3,100,74,0,NULL,20565,45000,DATE'2026-09-01','high','Rebate eligibility is suspended until invoices older than 60 days are cured'),
('RBT-2026-003-C','rebate_customer','PrimeCare Hospital Network','Zenith Medical Distribution Corp.','Southeast','active','FY2026 YTD','annual_net_spend_usd',1500000,1685000,112.3,93.2,0,0,NULL,218750,500000,DATE'2027-01-15','medium','Spend qualifies for the top tier but compliance is below the 95 percent requirement so eligibility should drop to the next lower tier');
