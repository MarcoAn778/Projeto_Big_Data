-- Execute como proprietário dos objetos de caged depois de criar caged_dashboard.
BEGIN;
GRANT USAGE ON SCHEMA caged TO caged_dashboard;
GRANT SELECT ON caged.v_indicadores_emprego TO caged_dashboard;
ALTER ROLE caged_dashboard SET default_transaction_read_only = on;
COMMIT;
