// realtime_audio_gateway.js
const WebSocket = require('ws');
const http = require('http');

const AZURE_REALTIME_ENDPOINT = process.env.AZURE_OPENAI_REALTIME_URL;
const AZURE_API_KEY = process.env.AZURE_OPENAI_API_KEY;

const server = http.createServer();
const wss = new WebSocket.Server({ server });

wss.on('connection', (clientWs) => {
  console.log('Client connected to Realtime Audio Gateway');

  // Establish upstream WebSocket to Azure OpenAI Realtime API
  const azureWs = new WebSocket(`${AZURE_REALTIME_ENDPOINT}?api-version=2024-10-01-preview&deployment=gpt-4o-realtime`, {
    headers: {
      'api-key': AZURE_API_KEY,
      'OpenAI-Beta': 'realtime=v1'
    }
  });

  azureWs.on('open', () => {
    // Send session configuration
    const sessionConfig = {
      type: 'session.update',
      session: {
        modalities: ['audio', 'text'],
        instructions: 'You are an enterprise voice concierge forSuisse Investment Banking. Maintain formal, crisp, executive tone.',
        voice: 'alloy',
        input_audio_format: 'pcm16',
        output_audio_format: 'pcm16',
        turn_detection: {
          type: 'server_vad',
          threshold: 0.5,
          prefix_padding_ms: 300,
          silence_duration_ms: 500
        }
      }
    };
    azureWs.send(JSON.stringify(sessionConfig));
  });

  // Relay client audio chunks to Azure
  clientWs.on('message', (message) => {
    if (azureWs.readyState === WebSocket.OPEN) {
      azureWs.send(message);
    }
  });

  // Relay Azure audio responses back to client
  azureWs.on('message', (data) => {
    if (clientWs.readyState === WebSocket.OPEN) {
      clientWs.send(data);
    }
  });

  clientWs.on('close', () => {
    azureWs.close();
  });
});

server.listen(8080, () => {
  console.log('Realtime Voice Gateway listening on port 8080');
});
