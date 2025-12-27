"""
Report Generator Service
Orchestrates report generation
"""
import os
import time
from datetime import datetime
from typing import Dict, Optional
from ..models import ReportTemplate, ReportExecution, SchemaModel
from ..extensions import db
from .report_query_builder import ReportQueryBuilder
from .report_export_service import ReportExportService


class ReportGenerator:
    """Main report generation orchestrator"""
    
    def __init__(self, reports_dir: str):
        self.query_builder = ReportQueryBuilder()
        self.exporter = ReportExportService(reports_dir)
        self.reports_dir = reports_dir
    
    def generate_report(
        self,
        template_id: int,
        format: str,
        user_id: int,
        params: Optional[Dict] = None
    ) -> ReportExecution:
        """
        Generate a report
        
        Args:
            template_id: Report template ID
            format: 'csv' or 'pdf'
            user_id: User requesting the report
            params: Runtime parameters to override config
        
        Returns:
            ReportExecution object
        """
        template = ReportTemplate.query.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        if not template.schema:
            raise ValueError("Template has no associated schema")
        
        # Create execution record
        execution = ReportExecution(
            template_id=template_id,
            user_id=user_id,
            trigger_type='manual',
            format=format,
            status='running',
            query_params=params or {}
        )
        db.session.add(execution)
        db.session.commit()
        
        try:
            start_time = time.time()
            
            # Build query config (merge template config with runtime params)
            query_config = self._merge_params(template.query_config or {}, params or {})
            
            # Build and execute query
            query = self.query_builder.build_query(query_config, template.schema)
            data = self.query_builder.execute_and_format(query, query_config, template.schema)
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"report_{template.id}_{execution.id}_{timestamp}.{format}"
            
            # Get fields: always use all fields if not explicitly set, to ensure vertical layout triggers
            fields = query_config.get('fields', [])
            if not fields and data:
                fields = list(data[0].keys())
            # If fields is set but incomplete, and data has more keys, use all keys
            if data and len(fields) < len(data[0].keys()):
                all_keys = list(data[0].keys())
                if set(fields) != set(all_keys):
                    fields = all_keys
            # Debug print
            import sys
            print(f"[PDF EXPORT] Fields used: {fields} (count: {len(fields)})", file=sys.stderr)
            
            # Export based on format
            if format == 'csv':
                filepath = self.exporter.export_csv(data, fields, filename)
            elif format == 'pdf':
                pdf_config = template.pdf_config or {}
                pdf_config['title'] = template.name
                pdf_config['filters'] = query_config.get('filters', [])
                filepath = self.exporter.export_pdf(data, fields, pdf_config, filename)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Update execution
            execution.completed_at = datetime.utcnow()
            execution.status = 'completed'
            execution.row_count = len(data)
            execution.file_path = filepath
            execution.file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            execution.execution_time_ms = int((time.time() - start_time) * 1000)
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            raise
        finally:
            db.session.commit()
        
        return execution
    
    def generate_adhoc_report(
        self,
        schema_id: int,
        query_config: dict,
        format: str,
        user_id: int,
        report_name: str = "Ad-hoc Report"
    ) -> ReportExecution:
        """
        Generate a report without a saved template
        
        Args:
            schema_id: Schema to query
            query_config: Query configuration
            format: 'csv' or 'pdf'
            user_id: User requesting the report
            report_name: Name for the report
        
        Returns:
            ReportExecution object
        """
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            raise ValueError(f"Schema {schema_id} not found")
        
        # Create execution record (no template)
        execution = ReportExecution(
            template_id=None,
            user_id=user_id,
            trigger_type='adhoc',
            format=format,
            status='running',
            query_params=query_config
        )
        db.session.add(execution)
        db.session.commit()
        
        try:
            start_time = time.time()
            
            # Build and execute query
            query = self.query_builder.build_query(query_config, schema)
            data = self.query_builder.execute_and_format(query, query_config, schema)
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"adhoc_{execution.id}_{timestamp}.{format}"
            
            # Get fields
            fields = query_config.get('fields', [])
            if not fields and data:
                fields = list(data[0].keys())
            
            # Export
            if format == 'csv':
                filepath = self.exporter.export_csv(data, fields, filename)
            elif format == 'pdf':
                pdf_config = query_config.get('pdf_config', {})
                pdf_config['title'] = report_name
                filepath = self.exporter.export_pdf(data, fields, pdf_config, filename)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Update execution
            execution.completed_at = datetime.utcnow()
            execution.status = 'completed'
            execution.row_count = len(data)
            execution.file_path = filepath
            execution.file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            execution.execution_time_ms = int((time.time() - start_time) * 1000)
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            raise
        finally:
            db.session.commit()
        
        return execution
    
    def _merge_params(self, base_config: dict, params: dict) -> dict:
        """Merge runtime parameters into base query config"""
        config = base_config.copy()
        
        # Override limit if provided
        if 'limit' in params:
            config['limit'] = params['limit']
        
        # Add/override filters
        if 'filters' in params:
            config['filters'] = config.get('filters', []) + params['filters']
        
        # Override fields
        if 'fields' in params:
            config['fields'] = params['fields']
        
        return config
