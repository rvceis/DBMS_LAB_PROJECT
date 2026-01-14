# Data Flow Diagrams (DFD) - Metadata Management System

## DFD Notation Key

- **Process**: Rectangle with rounded corners (P#)
- **Data Store**: Open-ended rectangle (D#)
- **External Entity**: Square (User, File, etc.)
- **Data Flow**: Arrow (→)

---

## Overview
This document provides comprehensive Data Flow Diagrams for the Metadata Management System, starting from the Context Diagram (Level 0) through the detailed process breakdown (Level 1).

---

## Level 0: Context Diagram

### System Boundary
The Metadata Management System is a centralized platform for managing metadata records with dynamic schemas, file uploads, and report generation.

### External Entities
1. **User** (Admin/Editor/Viewer)
2. **External Files** (Images, Videos, PDFs, Datasets)
3. **External Systems** (Optional integrations)

### Context Diagram

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
    User ───────────┤                                         │
     │              │    METADATA MANAGEMENT SYSTEM           │
     │  Login/      │                                         │
     │  Credentials │  • Schema Management                    │
     └─────────────►│  • Metadata Records                     │
                    │  • File Processing                      │
    Upload Files ──►│  • Report Generation                    │
     (Images,       │  • Analytics                            │
      Videos,       │                                         │
      PDFs)         │                                         │
                    │                                         │
    Reports ◄───────┤                                         │
    (CSV, PDF)      │                                         │
                    │                                         │
    Analytics ◄─────┤                                         │
    Data            │                                         │
                    └─────────────────────────────────────────┘
                              ▲           │
                              │           │
                              │           ▼
                         PostgreSQL    Stored Files
                         Database      (instance/uploads)
```

### Data Flows (Level 0)
1. **User → System**: Login credentials, schema definitions, metadata records, file uploads, queries
2. **System → User**: Authentication tokens, metadata records, reports, analytics, schemas
3. **External Files → System**: Images, videos, PDFs, CSV, JSON files
4. **System → Database**: CRUD operations on schemas, records, users
5. **Database → System**: Retrieved data
6. **System → File Storage**: Uploaded files
7. **File Storage → System**: File retrieval for viewing/download

---

## Level 1: First Level Decomposition

### Major Processes
---

## Level 2: DFD (Process Decomposition, with Data Stores)

### P3: Metadata Record Management (Level 2)

```
          +---------+
          |  User   |
          +----+----+
               |
               v
      +---------------------+
      | P3.1: Create Record |
      +----+----------------+
           |
           v
      +---------------------+
      | D6: Metadata Records|<<== Data Store
      +----+----------------+
           |
           v
      +---------------------+
      | D7: Field Values    |<<== Data Store
      +---------------------+
```

**Edges:**
- User → P3.1: Record data (name, schema_id, values)
- P3.1 → D6: Insert metadata record
- P3.1 → D7: Insert field values
- D6/D7 → User: Confirmation/Errors

---

### P4: File Processing & Upload (Level 2)

```
          +---------+
          |  User   |
          +----+----+
               |
               v
      +---------------------+
      | P4.1: File Upload   |
      +----+----------------+
           |
           v
      +---------------------+
      | P4.2: Metadata      |
      | Extraction          |
      +----+----------------+
           |
           v
      +---------------------+
      | D8: File Storage    |<<== Data Store
      +----+----------------+
           |
           v
      +---------------------+
      | D6: Metadata Records|<<== Data Store
      +---------------------+
```

**Edges:**
- User → P4.1: File
- P4.1 → P4.2: File for extraction
- P4.2 → D8: Store file
- P4.2 → D6: Create metadata record
- D6 → User: Confirmation

---

### P5: Report Generation (Level 2)

```
          +---------+
          |  User   |
          +----+----+
               |
               v
      +---------------------+
      | P5.1: Query Builder |
      +----+----------------+
           |
           v
      +---------------------+
      | D6: Metadata Records|<<== Data Store
      +----+----------------+
           |
           v
      +---------------------+
      | D7: Field Values    |<<== Data Store
      +----+----------------+
           |
           v
      +---------------------+
      | P5.3: CSV Export    |
      | P5.4: PDF Export    |
      +----+----------------+
           |
           v
      +---------------------+
      | D11: Report Files   |<<== Data Store
      +----+----------------+
           |
           v
      +---------+
      |  User   |
      +---------+
```

**Edges:**
- User → P5.1: Report request (filters, schema, format)
- P5.1 → D6/D7: Query records/fields
- P5.3/P5.4 → D11: Save report file
- D11 → User: Download link

---

## Level 3: DFD (Detailed Subprocess, with Data Stores)

### P3.1: Create Metadata Record (Level 3)

```
User
  |
  v
+---------------------+
| Validate Input      |
+---------+-----------+
          |
          v
+---------------------+
| D2: Schemas Table  |<<== Data Store
+---------+-----------+
          |
          v
+---------------------+
| Validate Field      |
| Values              |
+---------+-----------+
          |
          v
+---------------------+
| D6: Metadata Records|<<== Data Store
+---------+-----------+
          |
          v
+---------------------+
| D7: Field Values    |<<== Data Store
+---------+-----------+
          |
          v
+---------------------+
| Return Confirmation |
+---------------------+
```

**Edges:**
- User → Validate Input: Record data
- Validate Input → D2: Check schema exists
- D2 → Validate Field Values: schema fields
- Validate Field Values → D6: Insert record
- D6 → D7: Insert field values
- D7 → Return Confirmation: success

---

## Process Descriptions (Level 1)

### P1: User Authentication & Authorization

**Purpose**: Manage user access and permissions

**Inputs**:
- Login credentials (username, password)
- Registration data
- JWT tokens

**Outputs**:
- Authentication tokens
- User session data
- Authorization status

**Sub-processes**:
1. P1.1: User Registration
2. P1.2: User Login
3. P1.3: Token Validation
4. P1.4: Role-Based Access Control (Admin/Editor/Viewer)

**Data Stores**:
- D1: Users Table

**Logic**:
```
IF (username AND password valid) THEN
    Generate JWT token with user role
    Return token to user
ELSE
    Return authentication error
END IF

IF (user role = admin) THEN
    Grant full access
ELSE IF (user role = editor) THEN
    Grant create/edit/view access
ELSE IF (user role = viewer) THEN
    Grant view-only access
END IF
```

---

### P2: Schema Management

**Purpose**: Define and manage dynamic schemas for metadata records

**Inputs**:
- Schema definitions (name, asset type, fields)
- Field definitions (name, type, constraints)
- Schema modification requests

**Outputs**:
- Created/updated schemas
- Schema validation results
- Field configurations

**Sub-processes**:
1. P2.1: Create Schema
2. P2.2: Add/Modify Schema Fields
3. P2.3: Schema Versioning
4. P2.4: Schema Validation
5. P2.5: Auto-Schema Generation from Files

**Data Stores**:
- D2: Schemas Table
- D3: Schema Fields Table
- D4: Asset Types Table
- D5: Change Logs Table

**Logic**:
```
CREATE SCHEMA:
    Input: schema_name, asset_type_id, fields[]
    Validate schema_name is unique
    Create schema record
    FOR each field in fields:
        Validate field_type
        Create schema_field record with order_index
    END FOR
    Return schema_id

AUTO-GENERATE SCHEMA FROM FILE:
    Input: uploaded_file, asset_type_id
    Extract metadata from file (using MetadataExtractor)
    Infer field types from metadata values
    Suggest schema_name from filename
    Check existing schemas for matches
    IF match_score >= threshold:
        Return candidate schemas
    ELSE:
        Create new schema with inferred fields
    END IF
```

---

### P3: Metadata Record Management

**Purpose**: Create, read, update, and delete metadata records

**Inputs**:
- Metadata record data (name, schema_id, field values)
- Record queries (filters, search terms)
- Bulk import data

**Outputs**:
- Created/updated records
- Retrieved records
- Validation results

**Sub-processes**:
1. P3.1: Create Metadata Record
2. P3.2: Update Record Values
3. P3.3: Delete Record
4. P3.4: Query/Filter Records
5. P3.5: Bulk Data Import
6. P3.6: Field Value Validation

**Data Stores**:
- D6: Metadata Records Table
- D7: Field Values Table (EAV pattern)

**Logic**:
```
CREATE RECORD:
    Input: name, schema_id, field_values{}, asset_type_id
    Validate schema exists
    Get schema fields
    FOR each field in schema:
        IF field.is_required AND field not in field_values:
            Return validation error
        END IF
        Validate field_value against field_type and constraints
    END FOR
    Create metadata_record
    FOR each field_name, value in field_values:
        Create field_value record with appropriate type column
        (value_text, value_int, value_float, value_bool, value_date, value_json)
    END FOR
    Return record_id

VALIDATE FIELD VALUE:
    Input: value, field_type, constraints
    CASE field_type:
        WHEN 'integer': Ensure value is integer
        WHEN 'float': Ensure value is float
        WHEN 'boolean': Ensure value is true/false
        WHEN 'date': Parse date string
        WHEN 'json': Validate JSON structure
        WHEN 'array': Validate array format
        WHEN 'string': Apply length constraints
    END CASE
    IF constraints defined:
        Apply min/max/regex/enum validation
    END IF
```

---

### P4: File Processing & Upload

**Purpose**: Handle file uploads and extract metadata automatically

**Inputs**:
- Uploaded files (images, videos, PDFs, datasets)
- Asset type selection
- Schema selection

**Outputs**:
- Extracted metadata
- Auto-generated schemas
- Stored file references
- Metadata records

**Sub-processes**:
1. P4.1: File Upload & Validation
2. P4.2: Metadata Extraction (Images/Videos/PDFs)
3. P4.3: Schema Suggestion
4. P4.4: File Persistence
5. P4.5: Data Import (CSV/JSON parsing)

**Data Stores**:
- D8: File Storage (instance/uploads/)
- D2: Schemas Table
- D6: Metadata Records Table
- D7: Field Values Table

**Logic**:
```
SMART UPLOAD PHASE 1 (Suggest):
    Input: uploaded_file, asset_type_id
    Save to temporary location
    Extract metadata using MetadataExtractor:
        IF file is image:
            Extract width, height, format, EXIF data
        ELSE IF file is video:
            Extract duration, bitrate, codec
        ELSE IF file is PDF:
            Extract page_count, author, title
        ELSE IF file is JSON/CSV:
            Analyze structure and infer fields
        END IF
    
    Query existing schemas for asset_type_id
    FOR each schema:
        Calculate match_score = (common_fields / total_fields) * 100
    END FOR
    Sort schemas by match_score
    Return {metadata, suggested_fields, candidate_schemas}

SMART UPLOAD PHASE 2 (Commit):
    Input: uploaded_file, asset_type_id, action, schema_id OR schema_name
    
    IF action = 'use_existing':
        schema = Get schema by schema_id
    ELSE IF action = 'create_new':
        Create new schema with suggested_fields
        schema = newly created schema
    END IF
    
    Generate unique_filename = timestamp + original_filename
    Move file to instance/uploads/unique_filename
    
    metadata['file_path'] = 'instance/uploads/unique_filename'
    metadata['original_filename'] = original_filename
    
    Create metadata_record with schema_id
    FOR each field in schema.fields:
        IF field_name exists in metadata:
            Create field_value with extracted value
        END IF
    END FOR
    
    Return {success, schema_id, record_id}
```

---

### P5: Report Generation

**Purpose**: Generate CSV and PDF reports from metadata records

**Inputs**:
- Schema selection
- Query filters (date range, fields, conditions)
- Report format (CSV/PDF)
- Report template (optional)

**Outputs**:
- Generated reports (CSV/PDF files)
- Report execution history
- Download links

**Sub-processes**:
1. P5.1: Query Builder
2. P5.2: Data Aggregation
3. P5.3: CSV Export
4. P5.4: PDF Generation
5. P5.5: Report Template Management
6. P5.6: Report Execution Tracking

**Data Stores**:
- D6: Metadata Records Table
- D7: Field Values Table
- D9: Report Templates Table
- D10: Report Executions Table
- D11: Report Files (instance/reports/)

**Logic**:
```
GENERATE REPORT:
    Input: schema_id, filters, format, template_id (optional)
    
    Build SQL query from filters:
        SELECT fields FROM metadata_records
        JOIN field_values ON record_id
        WHERE schema_id = X
        AND field_value matches filter conditions
    
    Execute query and retrieve records
    
    IF format = 'csv':
        Generate CSV with headers and data rows
    ELSE IF format = 'pdf':
        Generate PDF using ReportLab:
            - Add title and metadata
            - Create table with headers
            - Add data rows
            - Apply styling
    END IF
    
    Save report to instance/reports/
    Create report_execution record with status and file_path
    
    IF async execution:
        Queue task with Celery
    END IF
    
    Return {execution_id, file_path, status}

DOWNLOAD REPORT:
    Input: execution_id
    Validate user has access
    Get report file_path from execution record
    Return file as download
```

---

### P6: Analytics & Insights

**Purpose**: Provide analytics and insights on metadata

**Inputs**:
- Asset type selection
- Date range
- Metrics selection

**Outputs**:
- Record counts by asset type
- Schema usage statistics
- Field type distribution
- Trend analysis

**Sub-processes**:
1. P6.1: Record Statistics
2. P6.2: Schema Analytics
3. P6.3: User Activity Tracking
4. P6.4: Data Quality Metrics

**Data Stores**:
- D6: Metadata Records Table
- D2: Schemas Table
- D1: Users Table
- D5: Change Logs Table

**Logic**:
```
GET ANALYTICS:
    Input: date_range, asset_type_id (optional)
    
    Count total records
    Count records by asset_type
    Count records by schema
    Count active vs inactive schemas
    Count records by user
    
    Calculate growth trends:
        Records created per day/week/month
    
    Analyze field usage:
        Most common field types
        Most populated fields
        Empty/null field rates
    
    Return {
        total_records,
        records_by_asset_type[],
        records_by_schema[],
        growth_trend[],
        field_statistics[]
    }
```

---

## Data Stores

### D1: Users Table
**Attributes**: id, username, email, password_hash, role, created_at
**Description**: Stores user account information and roles

### D2: Schemas Table
**Attributes**: id, name, version, asset_type_id, allow_additional_fields, is_active, created_by, created_at
**Description**: Stores schema definitions

### D3: Schema Fields Table
**Attributes**: id, schema_id, field_name, field_type, is_required, constraints, description, order_index, is_deleted
**Description**: Stores field definitions for each schema

### D4: Asset Types Table
**Attributes**: id, name, description, created_at
**Description**: Categories for schemas (e.g., Images, Videos, Documents)

### D5: Change Logs Table
**Attributes**: id, schema_id, change_type, description, change_details, changed_by, timestamp
**Description**: Audit trail for schema changes

### D6: Metadata Records Table
**Attributes**: id, name, schema_id, asset_type_id, created_by, tag, metadata_json, created_at, updated_at
**Description**: Main metadata records

### D7: Field Values Table (EAV Pattern)
**Attributes**: id, record_id, schema_field_id, value_text, value_int, value_float, value_bool, value_date, value_json
**Description**: Stores individual field values for each record

### D8: File Storage
**Location**: instance/uploads/
**Description**: Physical storage for uploaded files

### D9: Report Templates Table
**Attributes**: id, name, schema_id, query_config, created_by, created_at
**Description**: Saved report configurations

### D10: Report Executions Table
**Attributes**: id, template_id, schema_id, status, file_path, format, created_by, created_at
**Description**: Tracks report generation history

### D11: Report Files
**Location**: instance/reports/
**Description**: Generated CSV and PDF reports

---

## Data Flow Details

### Flow 1: User Authentication
```
User → [Login Credentials] → P1.2 (User Login)
P1.2 → [Query User] → D1 (Users Table)
D1 → [User Record] → P1.2
P1.2 → [Validate Password] → P1.3 (Token Validation)
P1.3 → [JWT Token] → User
```

### Flow 2: Schema Creation
```
User → [Schema Definition] → P2.1 (Create Schema)
P2.1 → [Validate Asset Type] → D4 (Asset Types)
P2.1 → [Insert Schema] → D2 (Schemas)
P2.1 → [Insert Fields] → D3 (Schema Fields)
P2.1 → [Log Change] → D5 (Change Logs)
P2.1 → [Created Schema] → User
```

### Flow 3: Smart File Upload
```
User → [Upload File] → P4.1 (File Upload)
P4.1 → [Extract Metadata] → P4.2 (Metadata Extraction)
P4.2 → [Query Schemas] → D2 (Schemas)
D2 → [Candidate Schemas] → P4.3 (Schema Suggestion)
P4.3 → [Suggestions] → User

User → [Choose Schema + Commit] → P4.4 (File Persistence)
P4.4 → [Save File] → D8 (File Storage)
P4.4 → [Create Record] → P3.1 (Create Metadata Record)
P3.1 → [Insert Record] → D6 (Metadata Records)
P3.1 → [Insert Field Values] → D7 (Field Values)
P3.1 → [Success] → User
```

### Flow 4: Report Generation
```
User → [Report Parameters] → P5.1 (Query Builder)
P5.1 → [Build Query] → P5.2 (Data Aggregation)
P5.2 → [Query Records] → D6 (Metadata Records)
P5.2 → [Query Field Values] → D7 (Field Values)
D6 + D7 → [Aggregated Data] → P5.3/P5.4 (Export)
P5.3/P5.4 → [Save Report] → D11 (Report Files)
P5.3/P5.4 → [Track Execution] → D10 (Report Executions)
P5.3/P5.4 → [Download Link] → User
```

### Flow 5: Metadata Query
```
User → [Query Filters] → P3.4 (Query/Filter Records)
P3.4 → [Query Records] → D6 (Metadata Records)
D6 → [Record IDs] → P3.4
P3.4 → [Query Field Values] → D7 (Field Values)
D7 → [Field Values] → P3.4
P3.4 → [Join Schema Fields] → D3 (Schema Fields)
D3 → [Field Definitions] → P3.4
P3.4 → [Formatted Records] → User
```

---

## Security Considerations

### Authentication Flow
```
Request → P1.3 (Token Validation)
P1.3 → [Validate JWT] → D1 (Users)
IF valid:
    Extract user_id and role
    Proceed to requested process
ELSE:
    Return 401 Unauthorized
END IF
```

### Authorization Matrix

| Role    | Schema Mgmt | Create Record | Edit Record | Delete Record | View Record | Generate Report | View Analytics |
|---------|-------------|---------------|-------------|---------------|-------------|-----------------|----------------|
| Admin   | ✓           | ✓             | ✓           | ✓             | ✓           | ✓               | ✓              |
| Editor  | ✗           | ✓             | ✓           | Own Only      | ✓           | ✓               | ✓              |
| Viewer  | ✗           | ✗             | ✗           | ✗             | ✓           | ✓               | ✓              |

---

## System Architecture Summary

### Technology Stack
- **Frontend**: React + TypeScript + Vite
- **Backend**: Flask + Python
- **Database**: PostgreSQL
- **File Storage**: Local filesystem (instance/)
- **Authentication**: JWT tokens
- **Task Queue**: Celery + Redis (for async reports)
- **PDF Generation**: ReportLab
- **Image Processing**: Pillow
- **PDF Processing**: PyPDF2

### Key Design Patterns
1. **Entity-Attribute-Value (EAV)**: For dynamic field storage
2. **Strategy Pattern**: For different file type processors
3. **Factory Pattern**: For report generators
4. **Repository Pattern**: For data access
5. **Service Layer**: For business logic separation

---

## Performance Considerations

### Optimizations
1. **Database Indexing**: On frequently queried fields (schema_id, asset_type_id)
2. **Lazy Loading**: Field values loaded only when needed
3. **Caching**: Schema definitions cached to reduce DB queries
4. **Async Processing**: Large reports generated asynchronously
5. **Pagination**: Record lists paginated (default 10-100 records)
6. **File Chunking**: Large file uploads handled in chunks

### Scalability
- Horizontal scaling for Flask workers
- Database read replicas for reporting
- CDN for static file delivery
- Message queue for background tasks
- File storage can be migrated to S3/cloud storage

---

## Conclusion

This DFD documentation provides a comprehensive view of the Metadata Management System's data flows, processes, and interactions. The system is designed to be flexible, scalable, and maintainable with clear separation of concerns across different processes.

**Version**: 1.0  
**Last Updated**: December 22, 2025
