/**
 * Architectural Drill 2: High-Performance PostHog Telemetry Relay
 */

const express = require('express');
const axios = require('axios');
const app = express();
app.use(express.json());

const POSTHOG_API_KEY = process.env.POSTHOG_API_KEY || "phc_live_98f12a...";
const POSTHOG_HOST = "https://app.posthog.com";

app.post('/api/v1/telemetry/event', (req, res) => {
    const { distinct_id, event_name, properties } = req.body;

    if (!distinct_id || !event_name) {
        return res.status(400).json({ error: "Missing required distinct_id or event_name" });
    }

    // Acknowledge immediately to Custom GPT to preserve sub-500ms conversational turn latency
    res.status(202).json({ status: "EVENT_QUEUED", timestamp: new Date().toISOString() });

    // Asynchronously dispatch to PostHog event queue
    setImmediate(async () => {
        try {
            await axios.post(`${POSTHOG_HOST}/capture/`, {
                api_key: POSTHOG_API_KEY,
                distinct_id: distinct_id,
                event: event_name,
                properties: {
                    ...properties,
                    source: "custom_gpt_action",
                    server_timestamp: Date.now()
                }
            }, { timeout: 3000 });
        } catch (err) {
            console.error("Telemetry forward failure:", err.message);
        }
    });
});
