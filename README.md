graph LR
    User[User<br/>Admin/Editor/Viewer]
    ExtFiles[External Files<br/>Images, Videos, PDFs, Datasets]
    ExtSys[External Systems]
    MMS[Metadata<br/>Management System]
    DB[(PostgreSQL<br/>Database)]
    Files[(Stored Files<br/>instance/uploads)]
    
    User -->|Login, Schema, Metadata| MMS
    MMS -.->|Reports, Analytics| User
    ExtFiles -->|File Uploads| MMS
    ExtSys -->|Integrations| MMS
    MMS -->|CRUD Operations| DB
    DB -.->|Retrieved Data| MMS
    MMS -->|Store Files| Files
    Files -. ->|Retrieve Files| MMS
    
    style User fill:#dae8fc
    style ExtFiles fill:#d5e8d4
    style ExtSys fill:#fff2cc
    style MMS fill:#fff,stroke:#000,stroke-width:3px
    style DB fill:#f5f5f5
    style Files fill:#f8cecc
