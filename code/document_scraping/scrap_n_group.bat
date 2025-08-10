@echo off

echo Running webdoc_scraper.py...
python webdoc_scraper.py uc_ai_scrap_config.yaml
if errorlevel 1 (
    echo webdoc_scraper.py failed, stopping script.
    exit /b 1
)

echo Running convert_to_RAG_ready_groups.py...
python convert_to_RAG_ready_groups.py uc_ai_scrap_config.yaml
if errorlevel 1 (
    echo convert_to_RAG_ready_groups.py failed, stopping script.
    exit /b 1
)
