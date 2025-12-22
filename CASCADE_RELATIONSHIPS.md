# Database Cascade Relationships Documentation

## Overview
This document explains how changes to Asset Types, Schemas, and Metadata Records automatically propagate through the system.

---

## Relationship Hierarchy

```
Asset Types
    ↓ (CASCADE DELETE, CASCADE UPDATE)
Schemas
    ↓ (CASCADE DELETE, CASCADE UPDATE)
Metadata Records
    ↓ (CASCADE DELETE, CASCADE UPDATE)
Field Values
```

---

## Detailed Cascade Rules

### 1. Asset Types → Schemas

**Foreign Key**: `schemas.asset_type_id` → `asset_types.id`

**ON DELETE CASCADE**:
- ✅ When you **delete an Asset Type**, all associated **Schemas are automatically deleted**
- Example: Delete "Images" asset type → All image schemas deleted

**ON UPDATE CASCADE**:
- ✅ When you **update an Asset Type ID**, all schema references update automatically
- This is rare but ensures referential integrity

**Python Relationship**:
```python
schemas = db.relationship('SchemaModel', cascade="all, delete-orphan")
```

---

### 2. Schemas → Schema Fields

**Foreign Key**: `schema_fields.schema_id` → `schemas.id`

**ON DELETE CASCADE**:
- ✅ When you **delete a Schema**, all associated **Schema Fields are automatically deleted**
- Example: Delete "Image Metadata" schema → All fields (width, height, format) deleted

**ON UPDATE CASCADE**:
- ✅ Schema ID changes propagate to all fields

**Python Relationship**:
```python
fields = db.relationship('SchemaField', cascade="all, delete-orphan")
```

---

### 3. Schemas → Metadata Records

**Foreign Key**: `metadata_records.schema_id` → `schemas.id`

**ON DELETE CASCADE**:
- ✅ When you **delete a Schema**, all associated **Metadata Records are automatically deleted**
- Example: Delete "Image Metadata" schema → All image records deleted
- **⚠️ WARNING**: This is destructive! All user data is lost.

**ON UPDATE CASCADE**:
- ✅ Schema ID changes propagate to all records

**Python Relationship**:
```python
metadata_records = db.relationship('MetadataRecord', cascade="all, delete-orphan")
```

**Alternative Approach (Safer)**:
If you want to prevent accidental data loss, you can change this to:
- `ON DELETE RESTRICT` - Prevents schema deletion if records exist
- `ON DELETE SET NULL` - Sets schema_id to NULL (requires nullable field)

---

### 4. Metadata Records → Field Values

**Foreign Key**: `field_values.record_id` → `metadata_records.id`

**ON DELETE CASCADE**:
- ✅ When you **delete a Metadata Record**, all associated **Field Values are automatically deleted**
- Example: Delete "photo.jpg" record → All field values (width=1920, height=1080) deleted

**ON UPDATE CASCADE**:
- ✅ Record ID changes propagate to all field values

**Python Relationship**:
```python
field_values = db.relationship('FieldValue', cascade="all, delete-orphan")
```

---

### 5. Schema Fields → Field Values

**Foreign Key**: `field_values.schema_field_id` → `schema_fields.id`

**ON DELETE CASCADE**:
- ✅ When you **delete a Schema Field**, all associated **Field Values are automatically deleted**
- Example: Remove "width" field from schema → All width values deleted from all records
- **Note**: We use soft delete (`is_deleted=True`) to prevent data loss

**ON UPDATE CASCADE**:
- ✅ Field ID changes propagate to all field values

**Python Relationship**:
```python
field_values = db.relationship('FieldValue', cascade="all, delete-orphan")
```

---

## Special Cases

### User References (ON DELETE SET NULL)

**Foreign Keys**:
- `schemas.created_by` → `users.id`
- `metadata_records.created_by` → `users.id`

**Behavior**:
- When you **delete a User**, their `created_by` references are set to `NULL`
- Schemas and records remain intact
- Audit trail preserved (created_at timestamp still exists)

---

### Asset Type References in Metadata (ON DELETE SET NULL)

**Foreign Key**: `metadata_records.asset_type_id` → `asset_types.id`

**Behavior**:
- When you **delete an Asset Type**, metadata records' `asset_type_id` is set to `NULL`
- Records remain accessible via schema
- Prevents data loss

---

### Parent Schema References (ON DELETE SET NULL)

**Foreign Key**: `schemas.parent_schema_id` → `schemas.id`

**Behavior**:
- When you **delete a parent Schema**, child schemas' `parent_schema_id` is set to `NULL`
- Child schemas remain independent
- Schema versioning preserved

---

## Practical Examples

### Example 1: Delete Asset Type

**Action**: Delete "Images" asset type

**Cascade Effect**:
```
1. "Images" Asset Type (DELETED)
   ↓
2. All schemas with asset_type_id=Images (DELETED)
   - "Image Metadata" schema
   - "Photo Properties" schema
   ↓
3. All schema fields in deleted schemas (DELETED)
   - width, height, format fields
   ↓
4. All metadata records using deleted schemas (DELETED)
   - "photo1.jpg" record
   - "photo2.jpg" record
   ↓
5. All field values in deleted records (DELETED)
   - width=1920, height=1080 values
```

**Result**: Complete cleanup, no orphan data

---

### Example 2: Delete Schema

**Action**: Delete "Image Metadata" schema

**Cascade Effect**:
```
1. "Image Metadata" Schema (DELETED)
   ↓
2. All schema fields (DELETED)
   - width, height, format
   ↓
3. All metadata records using this schema (DELETED)
   - "photo1.jpg", "photo2.jpg"
   ↓
4. All field values in deleted records (DELETED)
   - All width/height/format values
```

**Result**: Schema and all dependent data removed

---

### Example 3: Delete Metadata Record

**Action**: Delete "photo1.jpg" record

**Cascade Effect**:
```
1. "photo1.jpg" Metadata Record (DELETED)
   ↓
2. All field values for this record (DELETED)
   - width=1920
   - height=1080
   - format=JPEG
```

**Result**: Record and values removed, schema intact

---

### Example 4: Delete Schema Field (Soft Delete)

**Action**: Mark "width" field as `is_deleted=True`

**NO CASCADE**:
```
1. "width" Schema Field (is_deleted=True)
2. Field values preserved but hidden
3. Can be restored by setting is_deleted=False
```

**Result**: Field hidden, data preserved for rollback

---

### Example 5: Delete User

**Action**: Delete user "John Doe"

**Cascade Effect**:
```
1. User "John Doe" (DELETED)
   ↓
2. schemas.created_by=John → SET NULL
3. metadata_records.created_by=John → SET NULL
```

**Result**: User removed, but their created content remains with NULL creator

---

## Database Constraints Summary

| Relationship | ON DELETE | ON UPDATE | Python Cascade |
|--------------|-----------|-----------|----------------|
| AssetType → Schema | CASCADE | CASCADE | all, delete-orphan |
| Schema → SchemaField | CASCADE | CASCADE | all, delete-orphan |
| Schema → MetadataRecord | CASCADE | CASCADE | all, delete-orphan |
| Schema → ChangeLog | CASCADE | CASCADE | all, delete-orphan |
| MetadataRecord → FieldValue | CASCADE | CASCADE | all, delete-orphan |
| SchemaField → FieldValue | CASCADE | CASCADE | all, delete-orphan |
| User → Schema | SET NULL | - | - |
| User → MetadataRecord | SET NULL | - | - |
| AssetType → MetadataRecord | SET NULL | CASCADE | - |
| Schema → Schema (parent) | SET NULL | - | - |

---

## Safety Considerations

### ⚠️ High-Risk Operations

**1. Deleting Asset Types**
- Cascades to schemas and all metadata records
- **Recommendation**: Add confirmation dialog in UI
- **Alternative**: Implement soft delete (is_deleted flag)

**2. Deleting Schemas**
- Cascades to all metadata records
- **Recommendation**: Check record count before deletion
- **Alternative**: Set is_active=False instead of deleting

**3. Bulk Deletions**
- Can cascade to thousands of records
- **Recommendation**: Show impact preview before confirming
- **Alternative**: Implement batch operations with progress indicators

### ✅ Safe Operations

**1. Deleting Metadata Records**
- Only affects individual record and its field values
- No impact on schema or other records

**2. Soft Deleting Fields**
- Sets `is_deleted=True` without removing data
- Can be undone

**3. Deleting Users**
- Only sets `created_by` to NULL
- No data loss

---

## Migration Notes

### Applying Cascade Constraints

To apply these constraints to an existing database, run:

```bash
cd flask_backend
python -m flask db migrate -m "Add cascade constraints"
python -m flask db upgrade
```

### Rolling Back

If you need to revert:

```bash
python -m flask db downgrade
```

---

## Performance Implications

### Advantages
- ✅ Automatic cleanup (no orphan data)
- ✅ Maintains referential integrity
- ✅ Reduces storage usage
- ✅ Simplifies application logic

### Considerations
- ⚠️ Cascade deletes can be slow for large datasets
- ⚠️ No built-in undo for cascaded deletes
- ⚠️ Locks multiple tables during cascades
- ⚠️ Can cause unexpected data loss if not careful

### Optimization Tips
1. **Use Soft Deletes** for frequently "deleted" items
2. **Batch Operations** with proper indexing
3. **Archive Old Data** before mass deletions
4. **Monitor Cascade Depth** to avoid performance issues

---

## Testing Cascade Behavior

### Test 1: Delete Asset Type
```sql
-- Check current data
SELECT COUNT(*) FROM schemas WHERE asset_type_id = 1;
SELECT COUNT(*) FROM metadata_records WHERE asset_type_id = 1;

-- Delete asset type
DELETE FROM asset_types WHERE id = 1;

-- Verify cascade
SELECT COUNT(*) FROM schemas WHERE asset_type_id = 1; -- Should be 0
SELECT COUNT(*) FROM metadata_records WHERE schema_id IN 
    (SELECT id FROM schemas WHERE asset_type_id = 1); -- Should be 0
```

### Test 2: Delete Schema
```sql
-- Check current data
SELECT COUNT(*) FROM metadata_records WHERE schema_id = 1;
SELECT COUNT(*) FROM field_values WHERE record_id IN 
    (SELECT id FROM metadata_records WHERE schema_id = 1);

-- Delete schema
DELETE FROM schemas WHERE id = 1;

-- Verify cascade
SELECT COUNT(*) FROM metadata_records WHERE schema_id = 1; -- Should be 0
```

### Test 3: Delete Record
```sql
-- Check field values
SELECT COUNT(*) FROM field_values WHERE record_id = 1;

-- Delete record
DELETE FROM metadata_records WHERE id = 1;

-- Verify cascade
SELECT COUNT(*) FROM field_values WHERE record_id = 1; -- Should be 0
```

---

## Best Practices

### 1. Always Confirm Destructive Operations
```python
# Bad
def delete_schema(schema_id):
    schema = SchemaModel.query.get(schema_id)
    db.session.delete(schema)
    db.session.commit()

# Good
def delete_schema(schema_id):
    schema = SchemaModel.query.get(schema_id)
    record_count = len(schema.metadata_records)
    if record_count > 0:
        raise ValueError(f"Cannot delete schema with {record_count} records")
    db.session.delete(schema)
    db.session.commit()
```

### 2. Implement Soft Delete for Important Entities
```python
# Instead of deleting
schema.is_deleted = True
db.session.commit()

# Query only active
active_schemas = SchemaModel.query.filter_by(is_deleted=False).all()
```

### 3. Archive Before Mass Deletion
```python
# Export to backup before deleting
records = MetadataRecord.query.filter_by(schema_id=old_schema_id).all()
export_to_json(records, 'backup.json')

# Then safely delete
for record in records:
    db.session.delete(record)
db.session.commit()
```

### 4. Use Transactions for Safety
```python
try:
    db.session.delete(asset_type)
    db.session.commit()
except Exception as e:
    db.session.rollback()
    raise e
```

---

## Summary

**Automatic Cascading is Active** for:
- ✅ Asset Type deletions cascade to Schemas → Metadata Records → Field Values
- ✅ Schema deletions cascade to Schema Fields & Metadata Records → Field Values
- ✅ Metadata Record deletions cascade to Field Values
- ✅ All ID updates propagate automatically

**Benefits**:
- Clean database (no orphan records)
- Referential integrity enforced
- Simplified application logic

**Risks**:
- Accidental data loss if not careful
- Performance impact on large cascades
- No built-in recovery

**Recommendation**: Always implement confirmation dialogs and impact previews for delete operations in the UI.

---

**Version**: 1.0  
**Last Updated**: December 22, 2025
