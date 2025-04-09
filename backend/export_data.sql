-- Export data from Clients table
COPY (
    SELECT client_id, client_name, contact_person, email, phone, country, created_at, updated_at
    FROM clients
) TO '/tmp/clients_export.csv' WITH CSV HEADER;

-- Export data from Sales table
COPY (
    SELECT sales_id, sales_person, contact_person, reporting_manager, region, created_at, updated_at
    FROM sales
) TO '/tmp/sales_export.csv' WITH CSV HEADER;

-- Export data from Vendor Managers table
COPY (
    SELECT vm_id, vm_name, email, phone, created_at, updated_at
    FROM vendor_managers
) TO '/tmp/vendor_managers_export.csv' WITH CSV HEADER;

-- Export data from Partners table
COPY (
    SELECT partner_id, partner_name, contact_person, email, phone, country, created_at, updated_at
    FROM partners
) TO '/tmp/partners_export.csv' WITH CSV HEADER; 