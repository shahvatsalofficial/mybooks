/**
 * Enterprise Multimodal Voice + Video Streaming Engine
 * Streams 1 FPS camera snapshots alongside real-time microphone WebRTC audio.
 * Author: Vatsal Shah, Enterprise AI Architect
 */
export class MultimodalRealtimeAgent {
  private peerConnection: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private videoIntervalId: number | null = null;

  async startMultimodalSession(videoElement: HTMLVideoElement): Promise<void> {
    // 1. Establish WebRTC Audio Connection
    const tokenRes = await fetch("/api/realtime/session-token", { method: "POST" });
    const { client_secret } = await tokenRes.json();

    this.peerConnection = new RTCPeerConnection();
    const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.peerConnection.addTrack(micStream.getTracks()[0]);

    this.dataChannel = this.peerConnection.createDataChannel("oai-events");
    this.dataChannel.onopen = () => {
      console.log("✅ Data channel open. Initiating camera stream...");
      this.startCameraCapture(videoElement);
    };

    const offer = await this.peerConnection.createOffer();
    await this.peerConnection.setLocalDescription(offer);

    const sdpRes = await fetch("https://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview", {
      method: "POST",
      body: offer.sdp,
      headers: {
        Authorization: `Bearer ${client_secret.value}`,
        "Content-Type": "application/sdp"
      }
    });

    await this.peerConnection.setRemoteDescription({
      type: "answer",
      sdp: await sdpRes.text()
    });
  }

  private startCameraCapture(videoElement: HTMLVideoElement): void {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    // Capture 1 frame every 1,000 milliseconds (1 FPS)
    this.videoIntervalId = window.setInterval(() => {
      if (!this.dataChannel || this.dataChannel.readyState !== "open") return;

      canvas.width = videoElement.videoWidth || 640;
      canvas.height = videoElement.videoHeight || 480;
      ctx?.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

      // Convert to JPEG base64 string
      const base64Image = canvas.toDataURL("image/jpeg", 0.7).split(",")[1];

      // Inject visual frame into conversational context
      const imageEvent = {
        type: "conversation.item.create",
        item: {
          type: "message",
          role: "user",
          content: [
            {
              type: "input_image",
              image_url: {
                url: `data:image/jpeg;base64,${base64Image}`
              }
            }
          ]
        }
      };
      this.dataChannel.send(JSON.stringify(imageEvent));
    }, 1000);
  }

  stop(): void {
    if (this.videoIntervalId) clearInterval(this.videoIntervalId);
    this.peerConnection?.close();
  }
}
