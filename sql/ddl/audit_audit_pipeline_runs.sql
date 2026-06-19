CREATE TABLE IF NOT EXISTS workspace.audit.audit_pipeline_runs (
  audit_run_id STRING NOT NULL COMMENT 'Audit record ID',
  run_id STRING NOT NULL COMMENT 'Pipeline run ID',
  pipeline_name STRING NOT NULL COMMENT 'Pipeline name',
  run_timestamp TIMESTAMP NOT NULL COMMENT 'Run start time',
  run_duration_seconds INT COMMENT 'Duration in seconds',
  status STRING NOT NULL COMMENT 'SUCCESS, FAILED, PARTIAL',
  records_processed BIGINT COMMENT 'Total records processed',
  error_message STRING COMMENT 'Error details if failed',
  logged_at TIMESTAMP NOT NULL COMMENT 'Audit log timestamp',
  run_date DATE NOT NULL COMMENT 'Partition date derived from run_timestamp'
)
USING DELTA
PARTITIONED BY (run_date)
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);