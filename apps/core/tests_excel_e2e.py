"""Comprehensive End-to-End Excel Test Suite for airBersih ERP.

This module aggregates all E2E test tiers covering Excel Export, Template Download,
and Import across all 6 master data domains:
- Tier 1: Feature Coverage & Security (apps.core.tests_e2e.test_tier1_feature_coverage)
- Tier 2: Boundary & Corner Cases (apps.core.tests_e2e.test_tier2_boundary_cases)
- Tier 3: Duplicates & Error Reporting (apps.core.tests_e2e.test_tier3_duplicate_and_errors)
- Tier 4: Real-World Sequential Pipeline (apps.core.tests_e2e.test_tier4_realworld_pipeline)

To run the full suite:
    .venv\\Scripts\\python.exe manage.py test apps.core.tests_excel_e2e
"""

from apps.core.tests_e2e.test_tier1_feature_coverage import (
    ExcelAuthSecurityTests,
    ExcelExportFeatureTests,
    ExcelImportFeatureTests,
    ExcelTemplateFeatureTests,
)
from apps.core.tests_e2e.test_tier2_boundary_cases import (
    ExcelDataTypeValidationTests,
    ExcelEmptyFileBoundaryTests,
    ExcelForeignKeyAndDomainConstraintTests,
    ExcelHeaderIntegrityTests,
)
from apps.core.tests_e2e.test_tier3_duplicate_and_errors import (
    ExcelDatabaseDuplicateHandlingTests,
    ExcelInFileDuplicateTests,
    ExcelPartialErrorReportingTests,
)
from apps.core.tests_e2e.test_tier4_realworld_pipeline import (
    ExcelRealWorldPipelineTests,
)

__all__ = [
    "ExcelExportFeatureTests",
    "ExcelTemplateFeatureTests",
    "ExcelImportFeatureTests",
    "ExcelAuthSecurityTests",
    "ExcelEmptyFileBoundaryTests",
    "ExcelHeaderIntegrityTests",
    "ExcelDataTypeValidationTests",
    "ExcelForeignKeyAndDomainConstraintTests",
    "ExcelInFileDuplicateTests",
    "ExcelDatabaseDuplicateHandlingTests",
    "ExcelPartialErrorReportingTests",
    "ExcelRealWorldPipelineTests",
]
