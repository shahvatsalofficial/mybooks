#!/usr/bin/env python3
"""
AWS Industrial Cloud Series — Volume 2
Production Tool: Automated SSM Incident Post-Mortem Markdown Exporter
Author: Vatsal Shah
"""

import boto3
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("IncidentExporter")

class IncidentPostMortemExporter:
    def __init__(self, region_name: str = "us-east-1"):
        self.ssm_incidents = boto3.client('ssm-incidents', region_name=region_name)

    def generate_markdown_postmortem(self, incident_record_arn: str) -> str:
        """Fetches incident timeline and formats into standardized SRE post-mortem markdown."""
        logger.info(f"Generating post-mortem for incident: {incident_record_arn}")
        try:
            inc = self.ssm_incidents.get_incident_record(arn=incident_record_arn)['incidentRecord']
            title = inc.get('title', 'Unknown Incident')
            impact = inc.get('impact', 1)
            status = inc.get('status', 'RESOLVED')
            start_time = inc.get('creationTime').strftime("%Y-%m-%d %H:%M:%S UTC")
            end_time = inc.get('resolvedTime', datetime.now()).strftime("%Y-%m-%d %H:%M:%S UTC")

            md = f"""# Post-Mortem Report: {title}

| Attribute | Value |
| :--- | :--- |
| **Incident Status** | {status} |
| **Severity Level** | Sev-{impact} |
| **Start Time** | {start_time} |
| **Resolution Time** | {end_time} |

## Executive Summary
This document provides a blameless engineering review of incident '{title}'.

## Root Cause Analysis (5-Whys)
1. *Why did the system fail?*
2. *Why did safety mechanisms fail to catch it?*

## Corrective Action Items
* [ ] **P0**: Implement automated preventative guardrail.
* [ ] **P1**: Update CloudWatch SLO burn-rate alarm.
"""
            logger.info("✅ Post-Mortem markdown generated successfully.")
            return md
        except Exception as err:
            logger.error(f"Failed to generate post-mortem: {err}")
            return ""

if __name__ == "__main__":
    exporter = IncidentPostMortemExporter()
    print(exporter.generate_markdown_postmortem("arn:aws:ssm-incidents::112233445566:incident-record/prod-payment-outage/12345"))
