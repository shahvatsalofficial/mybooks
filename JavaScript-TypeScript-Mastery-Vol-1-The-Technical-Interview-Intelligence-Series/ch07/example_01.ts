// Vulnerable Lifecycle Event Ingestion
useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
        setMessages((prev) => [...prev, JSON.parse(event.data)]);
    };

    const socket = new WebSocket("wss://telemetry.enterprise.io/live");
    socket.addEventListener("message", handleMessage);
    
    // Fatal Error: Missing return cleanup function!
    // When this component unmounts, the socket remains open, and the listener
    // continues to run in the background, keeping the component alive in memory.
}, []);
