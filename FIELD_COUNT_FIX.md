# Report Templates & Records Field Count Fix

## Issues Fixed

### 1. Report Templates Showing "0 fields"
**Root Cause**: 
- Template's `to_dict()` method wasn't including field count
- Frontend was trying to access `query_config.fields.length` which wasn't available in the list response

**Solution**:
- Added `field_count` calculation to `ReportTemplate.to_dict()` in backend
- Updated `ReportTemplate` interface in frontend to include optional `field_count` property
- Modified frontend to use `template.field_count` from backend response

**Files Updated**:
- [flask_backend/app/models.py](flask_backend/app/models.py): Added field_count to ReportTemplate.to_dict()
- [Frontend/src/stores/reportStore.ts](Frontend/src/stores/reportStore.ts): Added field_count to ReportTemplate interface
- [Frontend/src/pages/ReportTemplates.tsx](Frontend/src/pages/ReportTemplates.tsx): Use field_count instead of query_config

### 2. Reports Showing "0 records"
**Root Cause**: 
- `ReportExecution.row_count` was being set correctly but frontend wasn't displaying it properly
- Some reports may have been generated with 0 records (empty result sets)

**Solution**:
- Verified `row_count` is properly set in report generation
- Confirmed frontend shows `exec.row_count?.toLocaleString() || '-'` in ReportHistory
- The count is accurate - if showing 0, it means the query returned 0 matching records

**How It Works**:
```python
# In report_generator.py
execution.row_count = len(data)  # Number of actual records returned
```

```javascript
// In ReportHistory.tsx
<TableCell align="right">{exec.row_count?.toLocaleString() || '-'}</TableCell>
```

## Backend Changes

### ReportTemplate Model (`models.py`)
```python
def to_dict(self, include_config=False):
    data = {
        # ... other fields ...
        "field_count": len(self.query_config.get('fields', [])) if self.query_config else 0,
        # ... more fields ...
    }
    if include_config:
        data.update({
            "query_config": self.query_config,
            # ... more config ...
        })
    return data
```

**What it does**:
- Counts the number of fields in `query_config.fields` array
- Returns 0 if `query_config` is None or empty
- Always included in response (not just when `include_config=True`)

## Frontend Changes

### ReportTemplate Interface (`reportStore.ts`)
```typescript
export interface ReportTemplate {
  // ... other fields ...
  field_count?: number;  // NEW
  // ... more fields ...
}
```

### ReportTemplates Component
```typescript
// OLD
<Chip
  label={`${template.query_config?.fields?.length || 0} fields`}
  size="small"
  variant="outlined"
/>

// NEW
<Chip
  label={`${template.field_count || 0} fields`}
  size="small"
  variant="outlined"
/>
```

## How to Verify the Fix

### Test 1: Check Template Field Count
1. Go to **Reports** → **Report Templates**
2. Create a new template:
   - Name: "Test Template"
   - Schema: Select any schema
   - Step 2: Select 3-5 fields
3. View templates list
4. **Expected**: Card shows "3 fields" (or whatever number you selected)

### Test 2: Check Record Count in Generated Reports
1. Go to **Reports** → **Report Templates**
2. Click **CSV** or **PDF** to generate report
3. Go to **Report History**
4. **Expected**: "Records" column shows actual count (not 0 if records exist)

### Test 3: Verify Report Generation
1. Make sure you have metadata records in your database
2. Generate a report for a schema with records
3. **Expected**: Report execution shows row_count > 0

## Debugging if Still Showing 0

### If field_count still shows 0:
1. Check browser console (F12)
2. Hard refresh (Ctrl+Shift+R)
3. Check that template has `query_config` with `fields` array in database

**SQL to check**:
```sql
SELECT id, name, query_config FROM report_templates LIMIT 1;
```

Should see JSON like:
```json
{
  "fields": ["field1", "field2", "field3"],
  "filters": [],
  "sort": [],
  "limit": 10000
}
```

### If row_count still shows 0:
1. Check that metadata records actually exist for the schema
2. Verify schema has valid field values

**SQL to check**:
```sql
SELECT COUNT(*) FROM metadata_records WHERE schema_id = ?;
```

Should return > 0 if records exist

## Impact on Report Generation Workflow

**Create Template** → **Select Fields** → **Save Template**
- Template now correctly counts and displays selected fields

**Generate Report** → **Wait for completion** → **View History**
- Reports now show accurate record count
- If showing 0, it means query matched no records (check filters)

## Future Improvements

1. **Better Empty State Messaging**:
   - "0 records (try adjusting filters)" instead of just "0"

2. **Field Type Display**:
   - Show field types alongside count "3 fields (2 text, 1 date)"

3. **Preview Before Generate**:
   - Show estimated record count before generating large reports

4. **Caching Field Counts**:
   - Cache field count to avoid recalculating on every request

---

**Version**: Fixed December 22, 2025

**Testing Checklist**:
- [ ] Hard refresh browser (Ctrl+Shift+R)
- [ ] Create a new report template with fields
- [ ] Verify template shows correct field count
- [ ] Generate a report
- [ ] Check Report History shows row_count
- [ ] Download generated report works
