#!/usr/bin/env python3
"""
AWS Network Firewall Suricata Rule Synchronizer & Flow Auditor
AWS Industrial Cloud Series — Volume 3
Author: Vatsal Shah (Enterprise Security & AI Architect)
"""

import boto3
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class SovereignNetworkFirewallManager:
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('network-firewall', region_name=region_name)
        self.region = region_name

    def build_suricata_rules(self, allowed_domains: List[str]) -> str:
        """
        Generates production-grade Suricata stateful rules.
        Enforces strict domain allowlists and blocks known threat vectors.
        """
        rules = [
            "# ========================================================",
            "# Sovereign Enterprise Suricata Stateful IPS Rule Set",
            "# AWS Network Firewall — Strict Evaluation Mode",
            "# ========================================================",
            "",
            "# 1. Drop all outbound cleartext HTTP traffic to external networks",
            'drop http $HOME_NET any -> $EXTERNAL_NET any (msg:"Block Cleartext HTTP Egress"; sid:1000010; rev:1;)',
            "",
            "# 2. Drop unauthorized DNS queries to non-approved external resolvers",
            'drop udp $HOME_NET any -> !10.0.0.2 53 (msg:"Block Rogue External DNS Queries"; sid:1000020; rev:1;)',
            ""
        ]

        sid_counter = 1000100
        for domain in allowed_domains:
            rule_pass = (
                f'pass tls $HOME_NET any -> $EXTERNAL_NET 443 '
                f'(msg:"Allow Egress TLS to {domain}"; tls_sni; content:"{domain}"; '
                f'nocase; endswith; sid:{sid_counter}; rev:1;)'
            )
            rules.append(rule_pass)
            sid_counter += 1

        rules.extend([
            "",
            "# 3. Default Drop for any unapproved external TLS connections",
            'drop tls $HOME_NET any -> $EXTERNAL_NET 443 (msg:"Block Unapproved TLS Egress"; sid:1000999; rev:1;)'
        ])

        return "\n".join(rules)

    def sync_rule_group(self, rule_group_name: str, suricata_rule_string: str) -> Dict[str, Any]:
        """
        Updates an existing stateful Suricata rule group in AWS Network Firewall.
        """
        logger.info(f"Synchronizing Suricata Rule Group [{rule_group_name}] in {self.region}...")
        desc = self.client.describe_rule_group(RuleGroupName=rule_group_name, Type='STATEFUL')
        update_token = desc['UpdateToken']
        
        response = self.client.update_rule_group(
            UpdateToken=update_token,
            RuleGroupName=rule_group_name,
            Type='STATEFUL',
            RuleGroup={
                'RulesSource': {
                    'RulesString': suricata_rule_string
                },
                'StatefulRuleOptions': {
                    'RuleOrder': 'STRICT_ORDER'
                }
            }
        )
        logger.info(f"Successfully updated rule group. New UpdateToken: {response['UpdateToken']}")
        return response

if __name__ == "__main__":
    approved_domains = [
        ".amazonaws.com",
        ".github.com",
        ".pypi.org",
        ".datadoghq.com"
    ]
    manager = SovereignNetworkFirewallManager()
    generated_rules = manager.build_suricata_rules(approved_domains)
    print("=== Generated Suricata Strict IPS Rules ===")
    print(generated_rules)
