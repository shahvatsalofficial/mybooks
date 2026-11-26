// realtime_audio_server.js — Sub-300ms Speech-to-Speech Streaming
const WebSocket = require('ws');
const https = require('https');

class AzureRealtimeAudioGateway {
    constructor(azureEndpoint, apiKey, deployment) {
        this.endpoint = azureEndpoint;
        this.apiKey = apiKey;
        this.deployment = deployment;
    }

    createSession(clientWs) {
        const targetUrl = `wss://${this.endpoint}/openai/realtime?api-version=2024-10-01-preview&deployment=${this.deployment}`;
        const aoaiWs = new WebSocket(targetUrl, {
            headers: {
                "api-key": this.apiKey,
                "OpenAI-Beta": "realtime=v1"
            }
        });

        aoaiWs.on('open', () => {
            console.log('Connected to Azure OpenAI Realtime Socket');
            // Configure Session Parameters
            aoaiWs.send(JSON.stringify({
                type: "session.update",
                session: {
                    modalities: ["audio", "text"],
                    voice: "alloy",
                    input_audio_format: "pcm16",
                    output_audio_format: "pcm16",
                    turn_detection: {
                        type: "server_vad",
                        threshold: 0.5,
                        prefix_padding_ms: 300,
                        silence_duration_ms: 200
                    }
                }
            }));
        });

        // Forward Audio Delta from Client to Azure
        clientWs.on('message', (data) => {
            if (aoaiWs.readyState === WebSocket.OPEN) {
                aoaiWs.send(data);
            }
        });

        // Forward Audio Delta from Azure to Client
        aoaiWs.on('message', (data) => {
            if (clientWs.readyState === WebSocket.OPEN) {
                clientWs.send(data);
            }
        });

        aoaiWs.on('close', () => clientWs.close());
        clientWs.on('close', () => aoaiWs.close());
    }
}

module.exports = AzureRealtimeAudioGateway;
