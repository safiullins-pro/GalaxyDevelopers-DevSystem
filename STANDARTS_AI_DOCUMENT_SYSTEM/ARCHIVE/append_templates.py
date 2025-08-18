import csv

templates_data = [
    # FIG templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/FIG/template_prototypes.fig_T062.json", "Description": "Template for Figma prototypes"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/FIG/template_wireframes.fig_T061.json", "Description": "Template for Figma wireframes"},
    # GENERIC templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/GENERIC/template_k8s_manifests_T077.json", "Description": "Generic Kubernetes manifests template"},
    # GITHUB templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/GITHUB/WORKFLOWS/", "Description": "Template for GitHub Actions workflows"},
    # HTML templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/HTML/template_coverage_report.html_T071.json", "Description": "Template for HTML coverage reports"},
    # IPA templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/IPA/template_release_build.ipa_T075.json", "Description": "Template for iOS release build IPA"},
    # JMX templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/JMX/template_load_test_plan.jmx_T072.json", "Description": "Template for JMeter load test plans"},
    # JSON templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/JSON/template_app_store_metadata_T067.json", "Description": "Template for App Store metadata JSON"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/JSON/template_monitoring_dashboard_T064.json", "Description": "Template for monitoring dashboard JSON"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/JSON/template_performance_benchmarks_T065.json", "Description": "Template for performance benchmarks JSON"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/JSON/template_tech_inventory_T066.json", "Description": "Template for technical inventory JSON"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/JSON/template_vulnerability_scan_T063.json", "Description": "Template for vulnerability scan JSON"},
    # MD templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_backup-strategy_T026.json", "Description": "Template for backup strategy Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_capacity_recommendations_T027.json", "Description": "Template for capacity recommendations Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_cli_specs_T021.json", "Description": "Template for CLI specifications Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_gaps_analysis_T028.json", "Description": "Template for gaps analysis Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_improvement_roadmap_T029.json", "Description": "Template for improvement roadmap Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_incident_response_plan_T024.json", "Description": "Template for incident response plan Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_interview_results_T019.json", "Description": "Template for interview results Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_migration_plan_T025.json", "Description": "Template for migration plan Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_pentest_results_T022.json", "Description": "Template for pentest results Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_review_notes_T030.json", "Description": "Template for review notes Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_rollback-procedures_T020.json", "Description": "Template for rollback procedures Markdown"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/MD/template_tech_stack_T023.json", "Description": "Template for tech stack Markdown"},
    # PDF templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_app_store_submission_T014.json", "Description": "Template for App Store submission PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_architecture_blueprint_T009.json", "Description": "Template for architecture blueprint PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_architecture_docs_T006.json", "Description": "Template for architecture documents PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_aso_strategy_T018.json", "Description": "Template for ASO strategy PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_coverage_matrix_T016.json", "Description": "Template for coverage matrix PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_design_system_T010.json", "Description": "Template for design system PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_er_diagrams_T011.json", "Description": "Template for ER diagrams PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_launch_report_T013.json", "Description": "Template for launch report PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_maturity_assessment_T017.json", "Description": "Template for maturity assessment PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_performance_report_T015.json", "Description": "Template for performance report PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_roles_mapping_T012.json", "Description": "Template for roles mapping PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_security_report_T008.json", "Description": "Template for security report PDF"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PDF/template_user_manual_T007.json", "Description": "Template for user manual PDF"},
    # PY templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_ai_test_framework.py_T047.json", "Description": "Template for AI test framework Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_api_client.py_T046.json", "Description": "Template for API client Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_compliance_checker.py_T058.json", "Description": "Template for compliance checker Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_composer_agent.py_T053.json", "Description": "Template for Composer Agent Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_data_processor.py_T048.json", "Description": "Template for data processor Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_distribution_engine.py_T051.json", "Description": "Template for distribution engine Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_document_service.py_T044.json", "Description": "Template for document service Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_integration_tests.py_T052.json", "Description": "Template for integration tests Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_integrator_agent.py_T056.json", "Description": "Template for Integrator Agent Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_notification_service.py_T049.json", "Description": "Template for notification service Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_publisher_agent.py_T055.json", "Description": "Template for Publisher Agent Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_quality_metrics.py_T050.json", "Description": "Template for quality metrics Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_research_agent.py_T054.json", "Description": "Template for Research Agent Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_reviewer_agent.py_T060.json", "Description": "Template for Reviewer Agent Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_style_validator.py_T045.json", "Description": "Template for style validator Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_sync_service.py_T057.json", "Description": "Template for sync service Python script"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/PY/template_template_engine.py_T059.json", "Description": "Template for template engine Python script"},
    # SH templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/SH/template_automation_scripts.sh_T074.json", "Description": "Template for automation shell scripts"},
    # SQL templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/SQL/template_database_schema_T035.json", "Description": "Template for database schema SQL"},
    # SWIFT templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/SWIFT/template_APIClient.swift_T037.json", "Description": "Template for API client Swift"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/SWIFT/template_AuthManager.swift_T043.json", "Description": "Template for Auth Manager Swift"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/SWIFT/template_CacheManager.swift_T039.json", "Description": "Template for Cache Manager Swift"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/SWIFT/template_DocumentModel.swift_T036.json", "Description": "Template for Document Model Swift"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/SWIFT/template_mock_framework.swift_T040.json", "Description": "Template for mock framework Swift"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/SWIFT/template_NetworkLayer.swift_T042.json", "Description": "Template for Network Layer Swift"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/SWIFT/template_SyncEngine.swift_T038.json", "Description": "Template for Sync Engine Swift"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/SWIFT/template_test_suite.swift_T041.json", "Description": "Template for test suite Swift"},
    # XCDATAMODELD templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/XCDATAMODELD/template_CoreDataModel.xcdatamodeld_T068.json", "Description": "Template for Core Data Model"},
    # XCFRAMEWORK templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/XCFRAMEWORK/template_shared_framework.xcframework_T073.json", "Description": "Template for shared framework"},
    # XCODEPROJ templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/XCODEPROJ/template_iOS_app.xcodeproj_T070.json", "Description": "Template for iOS app Xcode project"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/XCODEPROJ/template_macOS_app.xcodeproj_T069.json", "Description": "Template for macOS app Xcode project"},
    # XLSX templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/XLSX/template_compliance_matrix_T003.json", "Description": "Template for compliance matrix XLSX"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/XLSX/template_inventory_catalog_T005.json", "Description": "Template for inventory catalog XLSX"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/XLSX/template_keywords_research_T004.json", "Description": "Template for keywords research XLSX"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/XLSX/template_raci_matrix_T002.json", "Description": "Template for RACI matrix XLSX"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/XLSX/template_security_audit_T001.json", "Description": "Template for security audit XLSX"},
    # YAML templates
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/YAML/template_api_gateway.yaml_T033.json", "Description": "Template for API Gateway YAML"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/YAML/template_api_specs.yaml_T031.json", "Description": "Template for API specifications YAML"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/YAML/template_deployment-pipeline.yaml_T032.json", "Description": "Template for deployment pipeline YAML"},
    {"Category": "Templates & Standards", "Path": "03_TEMPLATES/YAML/template_monitoring-stack.yaml_T034.json", "Description": "Template for monitoring stack YAML"}
]

with open('inventory_catalog.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    for row_data in templates_data:
        writer.writerow([row_data['Category'], row_data['Path'], row_data['Description']])
