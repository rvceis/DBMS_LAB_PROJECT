"""
Celery tasks for async report generation
"""
from .celery_app import celery
from .extensions import db
from .services.report_generator import ReportGenerator
from .models import ReportExecution
import os


# Initialize report generator
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'reports')
report_gen = ReportGenerator(REPORTS_DIR)


@celery.task(name='generate_report_task')
def generate_report_task(template_id: int, format_type: str, user_id: int, params: dict = None):
    """
    Async task to generate a report
    
    Args:
        template_id: Report template ID
        format_type: 'csv' or 'pdf'
        user_id: User requesting the report
        params: Runtime parameters
    
    Returns:
        Execution ID
    """
    try:
        execution = report_gen.generate_report(template_id, format_type, user_id, params)
        return execution.id
    except Exception as e:
        # Log error
        print(f"Report generation failed: {e}")
        raise
