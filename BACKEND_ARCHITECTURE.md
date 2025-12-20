# MetaDB Backend - Complete Architecture & API Reference

## 🏗️ Database Schema & Models

### 1. **User** (`users` table)
```python
id: INT (PK)
username: STRING(128)
email: STRING(255) UNIQUE
password_hash: STRING(255)
role: STRING(50) ['admin', 'editor', 'viewer']
created_at: TIMESTAMP
```
**Relationships**: creator of schemas, metadata records, change logs
**Methods**: `to_dict()`

---

### 2. **AssetType** (`asset_types` table)
```python
id: INT (PK)
name: STRING(128) UNIQUE
description: TEXT
created_at: TIMESTAMP

# Relationship
schemas: List[SchemaModel]  # cascade delete
```
**Purpose**: Categorize metadata (e.g., "Image", "Video", "Document")
**Methods**: `to_dict()`

---

### 3. **SchemaModel** (`schemas` table) - CORE
```python
id: INT (PK)
name: STRING(255)
version: INT
asset_type_id: INT (FK → asset_types.id)  # Required - links schema to asset category
parent_schema_id: INT (FK → schemas.id, nullable)  # For schema inheritance/forking
allow_additional_fields: BOOLEAN (default=True)
is_active: BOOLEAN (default=True)
schema_json: JSON (nullable)  # Legacy storage, optional
created_by: INT (FK → users.id)
created_at: TIMESTAMP

# Relationships
fields: List[SchemaField]  # All field definitions (active + deleted)
metadata_records: List[MetadataRecord]  # Records using this schema
change_logs: List[ChangeLog]  # Audit trail
parent: SchemaModel  # Parent if forked
children: List[SchemaModel]  # Schemas forked from this
```
**Purpose**: Define schema structure with versioning and inheritance
**Methods**: `to_dict(include_fields=True)`

---

### 4. **SchemaField** (`schema_fields` table) - CORE
```python
id: INT (PK)
schema_id: INT (FK → schemas.id)
field_name: STRING(128)
field_type: STRING(50)  # string|integer|float|boolean|date|json|array|object
is_required: BOOLEAN
default_value: STRING(255)
constraints: JSON  # {min, max, regex, enum, min_length, max_length}
description: TEXT
is_deleted: BOOLEAN (default=False)  # Soft delete for rollback safety
order_index: INT  # Display order
created_at: TIMESTAMP

# UNIQUE constraint: (schema_id, field_name)
# Relationships
field_values: List[FieldValue]  # EAV values
```
**Purpose**: Individual field definitions in a schema
**Methods**: `to_dict()`

---

### 5. **MetadataRecord** (`metadata_records` table) - CORE
```python
id: INT (PK)
name: STRING(255) (default="Unnamed Record")
schema_id: INT (FK → schemas.id)  # Required - which schema validates this
asset_type_id: INT (FK → asset_types.id, nullable)
created_by: INT (FK → users.id)
tag: STRING(128)
metadata_json: JSON (nullable)  # Legacy storage, optional
created_at: TIMESTAMP
updated_at: TIMESTAMP (auto-update)

# Relationships
field_values: List[FieldValue]  # EAV storage (actual data)
```
**Purpose**: Individual metadata record instance
**Methods**: `to_dict(include_values=True)` → returns {id, name, schema_id, values: {field_name: value}}

---

### 6. **FieldValue** (`field_values` table) - EAV PATTERN
```python
id: INT (PK)
record_id: INT (FK → metadata_records.id)  # Which record
schema_field_id: INT (FK → schema_fields.id)  # Which field definition
value_text: TEXT
value_int: INTEGER
value_float: FLOAT
value_bool: BOOLEAN
value_date: DATETIME
value_json: JSON  # For arrays and complex objects
created_at: TIMESTAMP
updated_at: TIMESTAMP

# UNIQUE constraint: (record_id, schema_field_id)
```
**Purpose**: EAV storage - one row per field value in metadata
**Methods**: 
  - `get_value()` → returns typed value
  - `set_value(value)` → stores in appropriate column

---

### 7. **ChangeLog** (`change_logs` table)
```python
id: INT (PK)
schema_id: INT (FK → schemas.id, nullable)
change_type: STRING(64)  # created|updated|deleted|field_added|field_removed|field_modified|rollback
description: TEXT
change_details: JSON  # {field_name, old_type, new_type, affected_records, etc.}
schema_snapshot: JSON  # Complete schema state at this point (for rollback)
changed_by: INT (FK → users.id)
timestamp: TIMESTAMP
```
**Purpose**: Audit trail for schema modifications
**Methods**: `to_dict()`

---

### 8. **SchemaVersion** (`schema_versions` table)
```python
id: INT (PK)
schema_id: INT (FK → schemas.id)
version_number: INT
schema_snapshot: JSON  # {fields: [{id, name, type, required, constraints, ...}], ...}
change_summary: TEXT
created_by: INT (FK → users.id)
created_at: TIMESTAMP

# UNIQUE constraint: (schema_id, version_number)
```
**Purpose**: Complete versioned snapshots for rollback
**Methods**: `to_dict()`

---

## 📊 Entity Relationship Diagram

```
User (1) ──┬─→ (many) SchemaModel
           ├─→ (many) MetadataRecord
           ├─→ (many) ChangeLog
           └─→ (many) SchemaVersion

AssetType (1) ──→ (many) SchemaModel
               └─→ (many) MetadataRecord

SchemaModel (1) ──┬─→ (many) SchemaField
                  ├─→ (many) MetadataRecord
                  ├─→ (many) ChangeLog
                  ├─→ (many) SchemaVersion
                  └─→ (self) parent_schema_id

SchemaField (1) ──→ (many) FieldValue

MetadataRecord (1) ──→ (many) FieldValue
```

---

## 🔧 Services Layer

### **SchemaManager** - Core Schema Operations
**Location**: `app/services/schema_manager.py`

```python
SchemaManager:
  __init__()  # Thread-safe with per-schema locks
  
  # Create
  create_schema(name, asset_type_id, fields[], user_id, allow_additional_fields, parent_schema_id)
    → SchemaModel
  
  # Field Operations
  add_field(schema_id, field_name, field_type, user_id, is_required, default_value, constraints, description)
    → SchemaField
  
  remove_field(schema_id, field_name, user_id, permanent=False)
    → bool (soft delete by default, hard delete if permanent=True)
  
  modify_field(schema_id, field_name, user_id, new_type, new_required, new_constraints, new_description)
    → SchemaField
  
  fork_schema(schema_id, new_name, user_id, modifications)
    → SchemaModel (new schema inheriting from parent)
  
  # Helpers
  _get_schema_snapshot(schema) → dict
  _create_version_snapshot(schema, change_summary, user_id) → void
  _add_default_values_to_existing_records(field, default_value) → void
  _migrate_field_type(field, old_type, new_type) → void
```

**Thread Safety**: Uses `threading.RLock()` per schema_id to prevent concurrent modifications
**Transactions**: All ops wrapped in `db.session` with rollback on error

---

### **ValidationEngine** - Pre-flight Checks
**Location**: `app/services/validation_engine.py`

```python
ValidationEngine:
  SUPPORTED_TYPES = [string, integer, float, boolean, date, json, array, object]
  TYPE_COMPATIBILITY = {old_type: [compatible_new_types]}
  
  validate_fields(fields[]) → List[errors]
    Checks: name validity, duplicates, type support, constraints format
  
  validate_add_field(schema_id, field_def, record_count) → List[errors]
    Checks: required field must have default if records exist, performance warnings
  
  validate_type_change(field_id, old_type, new_type) → List[errors]
    Checks: compatibility, samples existing data for convertibility
  
  validate_constraints(field_id, constraints) → List[errors]
    Checks: constraint format, existing data against new constraints
  
  validate_field_removal(schema_id, field_name) → Dict
    Returns: {field_name, field_type, affected_values, non_null_values, data_loss, risk_level}
  
  # Helpers
  _is_valid_identifier(name) → bool
  _validate_constraints(field_name, field_type, constraints) → List[errors]
  _test_conversion(value, old_type, new_type) → void (throws on incompatible)
  _check_constraint_violation(value, field_type, constraints) → Optional[error_msg]
```

**Validation Types**:
  - Field naming (alphanumeric + underscore)
  - Type conversions (safe paths only)
  - Data compatibility (sample check on first 100 values)
  - Constraint format (min/max, regex, enum)

---

### **MetadataCatalog** - Caching Layer
**Location**: `app/services/metadata_catalog.py`

```python
MetadataCatalog(cache_ttl=300):  # 5-min default TTL
  
  # Schema Lookups (cached)
  get_schema(schema_id, use_cache=True) → Dict | None
  get_schemas_by_asset_type(asset_type_id, active_only, use_cache) → List[Dict]
  get_field(schema_id, field_name) → Dict | None
  get_fields(schema_id, include_deleted) → List[Dict]
  field_exists(schema_id, field_name) → bool
  
  # Asset Type Lookups (cached)
  get_asset_type(asset_type_id) → Dict | None
  get_all_asset_types() → List[Dict]
  
  # Stats
  get_schema_statistics(schema_id) → {schema_id, record_count, field_count, last_updated}
  
  # Cache Management
  invalidate_schema(schema_id) → void
  invalidate_asset_type(asset_type_id) → void
  clear_cache() → void
  get_cache_stats() → {size, keys, ttl}
  
  # Helpers
  _get_from_cache(key) → value | None
  _put_in_cache(key, value, ttl) → void
  _build_schema_dict(schema) → Dict
  _build_field_dict(field) → Dict
```

**Performance**: LRU-style caching with TTL expiration, per-key invalidation

---

### **SchemaVersionControl** - Versioning & Rollback
**Location**: `app/services/schema_version_control.py`

```python
SchemaVersionControl:
  
  # Version Access
  get_version(schema_id, version_number) → Dict | None
  get_latest_version(schema_id) → Dict | None
  list_versions(schema_id, limit=50) → List[Dict]
  
  # Comparison & History
  compare_versions(schema_id, v1, v2) → Dict
    Returns: {added_fields, removed_fields, modified_fields: {field_name: [changes]}, summary}
  
  get_change_history(schema_id, limit=100) → List[ChangeLog.to_dict()]
  get_field_history(schema_id, field_name) → List[changes]
  
  # Rollback (THE KEY FEATURE!)
  rollback(schema_id, target_version, user_id, preserve_data=True) → {success, message, from_version, to_version, changes}
    - If preserve_data=True: soft-deletes removed fields (data kept for 30 days by default)
    - If preserve_data=False: hard-deletes fields and associated data
    - Restores soft-deleted fields if rolling back past a deletion
  
  # Versioning
  create_snapshot(schema_id, user_id, change_summary) → SchemaVersion
  
  # Helpers
  _calculate_diff(snapshot1, snapshot2) → Dict
  _build_snapshot(schema) → Dict
```

**Safety**: All rollback operations happen within transaction; schema state updated only on success

---

### **MigrationGenerator** - SQL Generation
**Location**: `app/services/migration_generator.py`

```python
MigrationGenerator:
  
  # SQL Generation
  generate_migration(schema_id, from_version, to_version, dialect=postgresql) → str
    Generates: CREATE/ALTER statements for schema evolution
    Dialects: postgresql, mysql, sqlite
  
  generate_rollback_script(schema_id, target_version, dialect) → str
  
  generate_full_schema_ddl(schema_id, dialect) → str
    Returns: Complete CREATE TABLE with all current fields
  
  generate_data_migration(schema_id, from_version, to_version) → str
    Returns: Data conversion scripts for type changes
  
  # Helpers
  _generate_script_header(schema_id, from_version, to_version, diff) → str
  _generate_add_field_sql(table_name, field_def, dialect) → str
  _generate_modify_field_sql(table_name, from_field, to_field, dialect) → str
  _generate_remove_field_sql(table_name, field_name, dialect) → str
  _get_sql_type(field_type, dialect) → str (TYPE MAPPING)
  _format_default(value, field_type) → str


ImpactAnalyzer:
  
  analyze_field_addition(schema_id, field_def) → {operation, field_name, affected_records, estimated_time_seconds, storage_impact_mb, risk_level, requires_default, recommendations}
  
  analyze_field_removal(schema_id, field_name) → {operation, field_name, affected_values, non_null_values, data_loss, risk_level, recommendations}
  
  analyze_type_change(schema_id, field_name, new_type) → {operation, old_type, new_type, affected_values, validation_errors, risk_level, reversible, recommendations}
```

---

## 🔌 API Routes & Endpoints

### **Authentication** (`/auth`)
```
POST /auth/register
  Body: {username, email, password, role}
  Returns: {user, access_token}

POST /auth/login
  Body: {email, password}
  Returns: {user, access_token}
```

---

### **Asset Types** (`/asset-types`)
```
GET /asset-types
  Returns: [{id, name, description}]

POST /asset-types (admin)
  Body: {name, description?}
  Returns: {id, name}

PUT /asset-types/:id (admin)
  Body: {name}
  Returns: {id, name}

DELETE /asset-types/:id (admin)
  Returns: {message}
```

---

### **Schemas - CRUD** (`/schemas`)

#### List & Retrieve
```
GET /schemas?asset_type_id=:id&active_only=true
  Returns: [{id, name, version, asset_type_id, allow_additional_fields, is_active, fields: [...], statistics: {...}}]

GET /schemas/:id
  Returns: {id, name, version, asset_type_id, fields: [...], statistics}

GET /schemas/:id/fields?include_deleted=false
  Returns: [{id, field_name, field_type, is_required, constraints, ...}]
```

#### Create
```
POST /schemas (admin/editor)
  Body: {
    name: "ImageMetadata",
    asset_type_id: 1,
    fields: [
      {name: "title", type: "string", required: true, default: "Untitled"},
      {name: "width", type: "integer"},
      {name: "height", type: "integer"}
    ],
    allow_additional_fields: true,
    parent_schema_id: null
  }
  Returns: {success, schema: {...}}
```

#### Field Operations
```
POST /schemas/:id/fields (admin/editor)
  Body: {
    field_name: "author",
    field_type: "string",
    is_required: false,
    default_value: null,
    constraints: {max_length: 100},
    description: "Image author"
  }
  Returns: {success, field: {...}}

PUT /schemas/:id/fields/:field_name (admin/editor)
  Body: {type?, required?, constraints?, description?}
  Returns: {success, field: {...}}

DELETE /schemas/:id/fields/:field_name?permanent=false (admin/editor)
  Returns: {success, message}
```

#### Fork Schema
```
POST /schemas/:id/fork (admin/editor)
  Body: {
    name: "ImageMetadataV2",
    modifications: {
      add_fields: [{name: "license", type: "string"}],
      remove_fields: ["deprecated_field"]
    }
  }
  Returns: {success, schema: {...}}
```

---

### **Schemas - Versioning** (`/schemas/:id/versions`)

```
GET /schemas/:id/versions?limit=50
  Returns: [{version_number, schema_snapshot, change_summary, created_by, created_at}]

GET /schemas/:id/versions/:version_number
  Returns: {version_number, schema_snapshot, change_summary, created_by, created_at}

GET /schemas/:id/versions/compare?v1=1&v2=3
  Returns: {
    added_fields: ["author"],
    removed_fields: ["old_field"],
    modified_fields: {title: ["type: string → text"]},
    summary: {...}
  }

GET /schemas/:id/logs?limit=100
  Returns: [{change_type, description, change_details, changed_by_name, timestamp}]
```

#### Rollback
```
POST /schemas/:id/rollback (admin only)
  Body: {
    target_version: 2,
    preserve_data: true  # soft delete vs hard delete
  }
  Returns: {
    success: true,
    from_version: 5,
    to_version: 2,
    changes: ["Restored field 'author'", "Soft deleted field 'temp'"]
  }
```

---

### **Schemas - Migration & Analysis**

```
POST /schemas/:id/migration
  Body: {from_version: 1, to_version: 3, dialect: "postgresql"}
  Returns: {success, script: "ALTER TABLE ... ADD COLUMN ..."}

GET /schemas/:id/ddl?dialect=postgresql
  Returns: {ddl: "CREATE TABLE metadata_record_1 (...)"}

POST /schemas/:id/impact/add-field
  Body: {field: {name: "new_field", type: "string"}}
  Returns: {operation, affected_records, risk_level, recommendations}

GET /schemas/:id/impact/remove-field/:field_name
  Returns: {operation, affected_values, non_null_values, data_loss, risk_level}

POST /schemas/:id/impact/change-type/:field_name
  Body: {new_type: "float"}
  Returns: {operation, validation_errors, risk_level, reversible}
```

---

### **Metadata Records** (`/metadata`)

#### List & Retrieve
```
GET /metadata?asset_type=:id&limit=100
  Returns: [
    {
      id, name, schema_id, asset_type_id, asset_type_name,
      values: {field_name: value, ...},
      created_by, created_by_name, created_at
    }
  ]

GET /metadata/:id
  Returns: {id, name, schema_id, asset_type_id, values: {...}, created_at}
```

#### Create
```
POST /metadata (admin/editor)
  Body: {
    name: "photo_001.jpg",
    schema_id: 1,  # OR auto-find/create below
    asset_type_id: 1,
    values: {
      title: "Sunset",
      width: 1920,
      height: 1080,
      author: "John Doe"
    },
    tag: "nature",
    create_new_schema: false
  }
  Returns: {
    success, id, name, schema_id,
    values: {...},
    created_at
  }

# Auto-create schema on demand:
POST /metadata
  Body: {
    name: "video_001.mp4",
    asset_type_id: 2,
    values: {duration: 3600, format: "mp4", bitrate: 5000},
    create_new_schema: true
  }
  Returns: {success, schema auto-created, metadata record}
```

#### Suggest Matching Schemas
```
POST /metadata/suggest-schemas
  Body: {
    values: {title: "...", width: 800},  # OR metadata_json
    asset_type_id: 1  # optional, filters by asset type
  }
  Returns: {
    suggested_schemas: [
      {id, name, version, asset_type_id, fields, match_score: 85.5},
      ...
    ],
    incoming_keys: ["title", "width"]
  }
```

#### Update & Delete
```
PUT /metadata/:id (admin/editor on own records)
  Body: {name?, values?, tag?, schema_id?}
  Returns: {id, name, values, ...}

DELETE /metadata/:id (admin/editor)
  Returns: {message}
```

---

### **Analytics** (`/analytics`)

```
GET /analytics/dashboard
  Returns: {
    total_metadata_records, total_schemas, total_users,
    total_asset_types, recent_records_7days
  }

GET /analytics/metadata-by-asset-type
  Returns: [{name: "Image", value: 150}, {name: "Video", value: 45}]

GET /analytics/metadata-timeline
  Returns: [{date: "2025-01-01", records: 12}, ...]

GET /analytics/recent-activity
  Returns: [{activity_type, description, user, timestamp}]
```

---

### **Users** (`/users`)

```
GET /users/me
  Returns: {id, username, email, role}

GET /users (admin)
  Returns: [{id, username, email, role}]
```

---

## 🔐 Authentication & Authorization

**JWT Token**:
- Header: `Authorization: Bearer <token>`
- Payload: `{sub: user_id, role: "admin|editor|viewer"}`
- Expiry: Configured in Flask-JWT-Extended

**Role-Based Access Control (RBAC)**:
```
Admin:    Full access to all resources
Editor:   Can create/edit schemas and own metadata records
Viewer:   Read-only access to own metadata records
```

---

## 📥 Input/Output Examples

### Create Schema with Fields
**Request**:
```json
POST /schemas
{
  "name": "ProductMetadata",
  "asset_type_id": 2,
  "fields": [
    {
      "name": "sku",
      "type": "string",
      "required": true,
      "constraints": {"regex": "^[A-Z]{3}[0-9]{4}$"}
    },
    {
      "name": "price",
      "type": "float",
      "required": true,
      "constraints": {"min": 0, "max": 1000000}
    },
    {
      "name": "inStock",
      "type": "boolean",
      "required": false,
      "default_value": "true"
    },
    {
      "name": "tags",
      "type": "array",
      "required": false
    }
  ],
  "allow_additional_fields": false
}
```

**Response**:
```json
{
  "success": true,
  "schema": {
    "id": 5,
    "name": "ProductMetadata",
    "version": 1,
    "asset_type_id": 2,
    "allow_additional_fields": false,
    "is_active": true,
    "fields": [
      {
        "id": 24,
        "schema_id": 5,
        "field_name": "sku",
        "field_type": "string",
        "is_required": true,
        "constraints": {"regex": "^[A-Z]{3}[0-9]{4}$"},
        "order_index": 0,
        "is_deleted": false
      },
      ...
    ],
    "created_by": 1,
    "created_at": "2025-12-19T12:30:00"
  }
}
```

---

### Create Metadata Record
**Request**:
```json
POST /metadata
{
  "name": "Product Laptop XPS-2025",
  "schema_id": 5,
  "asset_type_id": 2,
  "values": {
    "sku": "LAP0001",
    "price": 1299.99,
    "inStock": true,
    "tags": ["electronics", "computers", "premium"]
  },
  "tag": "featured"
}
```

**Response**:
```json
{
  "id": 156,
  "name": "Product Laptop XPS-2025",
  "schema_id": 5,
  "asset_type_id": 2,
  "values": {
    "sku": "LAP0001",
    "price": 1299.99,
    "inStock": true,
    "tags": ["electronics", "computers", "premium"]
  },
  "tag": "featured",
  "created_by": 1,
  "created_at": "2025-12-19T14:45:00",
  "updated_at": "2025-12-19T14:45:00"
}
```

---

### Rollback Schema
**Request**:
```json
POST /schemas/5/rollback
{
  "target_version": 1,
  "preserve_data": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully rolled back to version 1",
  "from_version": 3,
  "to_version": 1,
  "changes": [
    "Soft deleted field 'tags' (column will be available for 30 days)",
    "Restored field 'price'"
  ]
}
```

---

## 🔄 Data Flow Example: Creating Metadata with Auto-Schema

1. **User submits metadata** with `asset_type_id` but no `schema_id`
2. **Backend** calls `find_best_schema_from_keys()` to find matching schema
3. **If no match** and `create_new_schema=true`, calls `SchemaManager.create_schema()`
   - Infers types from values
   - Creates SchemaField rows
   - Creates SchemaVersion for v1
   - Logs "auto_created" change
4. **Creates MetadataRecord** linked to schema
5. **For each field value**, creates FieldValue row in EAV table
6. **Returns** metadata record with flattened `values` dict

---

## 🚀 Key Capabilities

| Feature | Status | Details |
|---------|--------|---------|
| **Dynamic Schema Creation** | ✅ | Runtime schema definition without predefined structure |
| **Field Management** | ✅ | Add/remove/modify fields on live schemas |
| **Type Safety** | ✅ | Type-aware storage (separate columns per type) + validation |
| **Soft Deletes** | ✅ | Fields marked deleted but data preserved (30-day retention) |
| **Schema Versioning** | ✅ | Complete snapshots for every change |
| **Rollback** | ✅ | Revert to any previous version with data safety options |
| **Schema Inheritance** | ✅ | Fork/extend schemas from existing ones |
| **Impact Analysis** | ✅ | Risk assessment before modifications |
| **Migration Scripts** | ✅ | Auto-generate SQL for PostgreSQL/MySQL/SQLite |
| **Caching** | ✅ | LRU cache with TTL for performance |
| **Thread Safety** | ✅ | Per-schema locks to prevent concurrent modification conflicts |
| **RBAC** | ✅ | Admin/editor/viewer role-based access |
| **Audit Trail** | ✅ | Complete change history with who/what/when |
| **Auto-Schema Creation** | ✅ | Infer schema from incoming metadata |

---

## 📝 Error Handling

All endpoints return consistent error format:
```json
{
  "error": "description"
}
```

HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient role)
- `404` - Not found
- `500` - Server error

---

Now ready for frontend implementation! Please let me know:
1. **Which pages/components** you need
2. **What user flows** to support
3. **UI/UX preferences** (forms, modals, inline editing, etc.)
4. **Data visualization needs** (charts, tables, comparisons)
