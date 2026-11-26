/**
 * Architectural Drill 4: Slack Interactive HITL Escalation Dispatcher
 */

const express = require('express');
const axios = require('axios');
const app = express();
app.use(express.json());

const SLACK_WEBHOOK_URL = process.env.SLACK_LEGAL_WEBHOOK || "https://hooks.slack.com/services/T00/B00/X00";

app.post('/api/v1/escalations/slack', async (req, res) => {
    const { contract_id, counterparty, risk_clause, severity, proposed_redline } = req.body;

    const slackCard = {
        blocks: [
            {
                type: "header",
                text: { type: "plain_text", text: `🚨 Legal Escalation: ${severity} Risk Detected` }
            },
            {
                type: "section",
                fields: [
                    { type: "mrkdwn", text: `*Contract ID:*\n${contract_id}` },
                    { type: "mrkdwn", text: `*Counterparty:*\n${counterparty}` }
                ]
            },
            {
                type: "section",
                text: { type: "mrkdwn", text: `*Flagged Clause:*\n>${risk_clause}` }
            },
            {
                type: "section",
                text: { type: "mrkdwn", text: `*Proposed Redline:*\n${proposed_redline}` }
            },
            {
                type: "actions",
                elements: [
                    {
                        type: "button",
                        text: { type: "plain_text", text: "Approve Redline" },
                        style: "primary",
                        value: `approve_${contract_id}`
                    },
                    {
                        type: "button",
                        text: { type: "plain_text", text: "Escalate to Partner" },
                        style: "danger",
                        value: `escalate_${contract_id}`
                    }
                ]
            }
        ]
    };

    try {
        await axios.post(SLACK_WEBHOOK_URL, slackCard);
        res.status(200).json({ status: "ESCALATION_DISPATCHED", contract_id });
    } catch (err) {
        res.status(500).json({ error: "Failed to dispatch Slack card", detail: err.message });
    }
});
