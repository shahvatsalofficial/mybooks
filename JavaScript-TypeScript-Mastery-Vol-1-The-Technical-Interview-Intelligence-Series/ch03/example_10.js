// Optimized Implementation: Self-Cleaning Subscriptions
class CleanTelemetryPanel extends React.Component {
    constructor(props) {
        super(props);
        this.handleMessage = this.handleMessage.bind(this);
    }

    componentDidMount() {
        this.socket = new WebSocket('ws://telemetry.enterprise.internal');
        this.socket.addEventListener('message', this.handleMessage);
    }

    componentWillUnmount() {
        if (this.socket) {
            // Close connection and clean up listener
            this.socket.removeEventListener('message', this.handleMessage);
            this.socket.close();
            this.socket = null;
        }
    }

    handleMessage(event) {
        this.setState({ metrics: JSON.parse(event.data) });
    }
}
