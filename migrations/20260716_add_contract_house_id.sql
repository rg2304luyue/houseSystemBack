-- Run once before deploying the contract/rental association fix.
ALTER TABLE contract ADD COLUMN houseId INT NULL;
CREATE INDEX ix_contract_houseId ON contract (houseId);

-- Legacy contracts have no house reference. Their rental record is the only
-- historical source; match tenant, landlord and creation date before enabling
-- the new per-house query. Ambiguous same-day duplicates require manual audit.
UPDATE contract AS c
JOIN rental AS r
  ON r.tenant_username = c.tenantName
 AND r.landlord_username = c.landlordName
 AND DATE(r.currentDate) = DATE(c.currentDate)
SET c.houseId = r.house_id
WHERE c.houseId IS NULL;
