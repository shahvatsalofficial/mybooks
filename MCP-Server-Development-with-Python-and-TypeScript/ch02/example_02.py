class Transport(ABC):
    @abstractmethod
    async def start(self) -> None:
        """Initialize underlying sockets, streams, or child processes."""
        ...

    @abstractmethod
    async def send(self, message: JSONRPCMessage) -> None:
        """Transmit a discrete JSON-RPC message envelope over the wire."""
        ...

    @abstractmethod
    async def receive_stream(self) -> AsyncIterator[JSONRPCMessage]:
        """Yield parsed JSON-RPC messages arriving from the remote peer."""
        ...
