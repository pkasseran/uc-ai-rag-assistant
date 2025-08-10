#!/bin/bash
echo "Running webdoc_scraper.py..."
python webdoc_scraper.py uc_ai_scrap_config.yaml
if [ $? -ne 0 ]; then
  echo "webdoc_scraper.py failed, stopping script."
  exit 1
fi

echo "Running convert_to_RAG_ready_groups.py..."
python convert_to_RAG_ready_groups.py uc_ai_scrap_config.yaml
if [ $? -ne 0 ]; then
  echo "convert_to_RAG_ready_groups.py failed, stopping script."
  exit 1
fi