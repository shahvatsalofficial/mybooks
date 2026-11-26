// Production WebRTC Configuration with Enterprise STUN/TURN Relays
const rtcConfiguration: RTCConfiguration = {
  iceServers: [
    {
      urls: ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]
    },
    {
      urls: ["turn:turn.enterprise-gateway.com:443?transport=tcp"],
      username: "enterprise_voice_client",
      credential: "secure_dynamic_auth_token_xyz"
    }
  ],
  iceTransportPolicy: "all", // Permitted to use direct or relayed candidates
  bundlePolicy: "max-bundle"  // Mux audio and data channels over a single transport
};
