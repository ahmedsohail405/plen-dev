# Lead contract: Plen Dev CMS <-> audit server
See PIPELINE.md section 4 (single source of truth). Agreed with the site/CMS thread on 2026-11-17: Payload CMS, afterChange webhook on create for every lead type, HMAC-signed, PATCH /api/leads/:id with Bearer CMS_API_TOKEN scoped to audit_* fields.
