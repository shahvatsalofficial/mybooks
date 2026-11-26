// Vulnerable Implementation: Uncleaned WebSocket Leaks
class TelemetryPanel extends React.Component {
    componentDidMount() {
        // Establish connection to streaming data source
        this.socket = new WebSocket('ws://telemetry.enterprise.internal');
        
        // VULNERABILITY: Registering event handlers that retain component references
        this.socket.addEventListener('message', (event) => {
            this.handleIncomingData(event.data);
        });
    }

    componentWillUnmount() {
        // VULNERABILITY: The component unmounts, but the socket is not closed,
        // and the event listener is not removed. The socket remains open,
        // and its event listener keeps the component instance alive in memory.
    }

    handleIncomingData(data) {
        this.setState({ metrics: JSON.parse(data) });
    }
}
