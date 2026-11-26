/**
 * Production Enterprise WebRTC Realtime Voice Client
 * Author: Vatsal Shah, Enterprise AI Architect
 */
export class RealtimeVoiceAssistant {
  private peerConnection: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private audioElement: HTMLAudioElement;

  constructor() {
    this.audioElement = document.createElement("audio");
    this.audioElement.autoplay = true;
  }

  async startSession(): Promise<void> {
    console.log("1. Requesting ephemeral token from enterprise backend...");
    const tokenResponse = await fetch("/api/realtime/session-token", { method: "POST" });
    const { client_secret } = await tokenResponse.json();
    const ephemeralKey = client_secret.value;

    console.log("2. Initializing WebRTC RTCPeerConnection...");
    this.peerConnection = new RTCPeerConnection();

    // Attach remote audio track from OpenAI to playback element
    this.peerConnection.ontrack = (event) => {
      console.log("🔊 Received remote audio stream from model!");
      this.audioElement.srcObject = event.streams[0];
    };

    // Capture microphone input
    const localStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 24000
      }
    });
    this.peerConnection.addTrack(localStream.getTracks()[0]);

    // Create Data Channel for JSON control events
    this.dataChannel = this.peerConnection.createDataChannel("oai-events");
    this.dataChannel.onmessage = (event) => {
      const serverEvent = JSON.parse(event.data);
      this.handleServerEvent(serverEvent);
    };

    // Create SDP Offer
    const offer = await this.peerConnection.createOffer();
    await this.peerConnection.setLocalDescription(offer);

    // Send SDP Offer to OpenAI Realtime Endpoint
    const baseUrl = "https://api.openai.com/v1/realtime";
    const model = "gpt-4o-realtime-preview";
    const sdpResponse = await fetch(`${baseUrl}?model=${model}`, {
      method: "POST",
      body: offer.sdp,
      headers: {
        Authorization: `Bearer ${ephemeralKey}`,
        "Content-Type": "application/sdp"
      }
    });

    const answerSdp = await sdpResponse.text();
    const answer: RTCSessionDescriptionInit = {
      type: "answer",
      sdp: answerSdp
    };

    // Finalize Peer Connection with SDP Answer
    await this.peerConnection.setRemoteDescription(answer);
    console.log("✅ WebRTC Peer Connection Established! Voice Assistant Live.");
  }

  private handleServerEvent(event: any): void {
    if (event.type === "input_audio_buffer.speech_started") {
      console.log("⚡ User Interruption Detected! Halting speaker output.");
      this.audioElement.pause();
      this.audioElement.currentTime = 0;
    }
  }

  stopSession(): void {
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }
    console.log("Voice Assistant session terminated.");
  }
}
