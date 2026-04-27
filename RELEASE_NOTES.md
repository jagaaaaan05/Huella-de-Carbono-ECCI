# Release Notes

## Version
- Release: v1.0.0-rc1
- Date: 2026-04-27
- Repository: Huella-de-Carbono-ECCI

## Executive Summary
This release consolidates the platform into a backend-official calculation model with auditable runs, historical traceability, robust CSV export, and production-oriented project hygiene.

## Key Delivered Outcomes

### 1. Official backend calculation flow
- Inventory execution centralized in backend run endpoint.
- Frontend aligned to official run model from Huella screen.
- Operational tables set to reference/export behavior for consistency.

### 2. Auditable run persistence and history
- Calculation runs are persisted with source-level traces.
- History endpoint supports filtering and ordering for operational analysis.
- Database indexing added to improve historical query performance.

### 3. UI and UX consistency improvements
- Operational screens include explicit official-mode notice.
- Local calculate and row-mutation actions removed from operational tables.
- Table experience focused on data reference and CSV export.

### 4. CSV export hardening
- UTF-8 BOM support for Excel compatibility.
- Safe escaping and improved formatting.
- Structured file naming by section and timestamp.

### 5. Data entry reliability
- Dropdown hydration expanded with missing variable and unit options.
- Unit catalogs mapped by source context to avoid empty selectors.

### 6. Documentation and release readiness
- README updated with official operation model and endpoint guidance.
- Preproduction checklist added for go-live governance.
- UI E2E regression checklist added for repeatable validation.

## Validation Snapshot
- Django tests: 23/23 passing.
- Django check: no issues.
- Runtime UI verification completed for official-mode behavior.

## Operational Notes
- Current API permission mode is prototype-oriented for ease of use; tighten auth for production.
- Production deployment should follow the preproduction checklist and rollback plan.

## Main Artifacts
- docs/audits/CHECKLIST_PREPRODUCCION.md
- docs/audits/REGRESION_UI_E2E.md
- docs/audits/FASE2_MODELO.md
- README.md

## Next Recommended Step
- Create a tagged release after final UAT sign-off and production auth hardening.
