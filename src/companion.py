"""Socket logic to communicate with a companion app over a TCP Socket."""

import logging
import socket

import utils
from console import Console


_log = logging.getLogger(__name__)
_log.addHandler(utils.HANDLER)
_log.setLevel(logging.INFO)


class Server:
    """Simple single client server over a socket that sends/receives
    messages in lines (terminated by '/n') of Strings."""

    def __init__(self, hostname: str, port: int):
        """Creates a simple single client server over a socket that sends/receives
        messages in lines (terminated by '/n') of Strings.

            Args:
                hostname (str): Hostname of the server socket.
                port (int): Port to open the server socket on.
        """

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )  # Allow reused afterwards
        self.server_socket.bind((hostname, port))
        self.server_socket.listen(1)
        self.client_socket, self.address = None, None
        self.buffer = []

    class ConnectionBrokenException(Exception):
        """Explicit exception raised when the connection to the client
        is broken.
        """

    @utils.to_thread
    def connect(self):
        """Awaits a client connection."""
        (self.client_socket, self.address) = self.server_socket.accept()

    def disconnect(self):
        """Disconnects the client and server sockets."""

        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()
        if self.client_socket:
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()

    def receive_line(self) -> str:
        """Receive the next string terminated by a newline character.

        Receives bytes of information, in chunks of 1024, from the client socket,
        until a newline character is reached. Bytes of characters that were received,
        but not part of the String being terminated by the newline character
        will be saved in the `self.buffer` for the next receive_line call to read.

        Raises:
            Server.ConnectionBrokenException: If the connection was terminated before a
            full line was received.

        Returns:
            str: Decoded string message  sent from the client.
        """

        chunks = []

        while len(self.buffer) > 0:
            buffered = self.buffer.pop()
            if b"\n" in buffered:
                i = buffered.index(b"\n")
                chunks.append(buffered[:i])
                self.buffer.append(buffered[i + 1 :])
                return b"".join(chunks).decode()
            chunks.append(buffered)

        while True:
            chunk = self.client_socket.recv(1024)
            if not chunk:
                raise Server.ConnectionBrokenException()

            if b"\n" in chunk:
                i = chunk.index(b"\n")
                chunks.append(chunk[:i])
                self.buffer.append(chunk[i + 1 :])
                return b"".join(chunks).decode()
            chunks.append(chunk)

    def send_line(self, msg: str):
        """Sends a message over the socket to the client.

        If the message is not terminated by a newline, one will be added, before it is encoded.


        Args:
            msg (str): Unencoded string message to send over the socket to the client.

        Raises:
            Server.ConnectionBrokenException: If the connection was terminated before
            a full line was sent, which is realised when 0 bytes of the message
            have sent over the socket after a `socket.send` call.
        """

        if not msg.endswith("\n"):
            msg = msg + "\n"
        msg = msg.encode()

        total_sent = 0
        while total_sent < len(msg):
            sent = self.client_socket.send(msg[total_sent:])
            if sent == 0:
                raise Server.ConnectionBrokenException()
            total_sent = total_sent + sent


class CompanionConsole:
    """Extension of the Console class that can receive commands
    over a Socket.
    """

    def __init__(self, console: Console, hostname: str, port: int):
        """Creates an extension of the Console class that receives input
        for commands via a TCP Socket.

        Args:
            console (Console): Console to send input to.
            hostname (str): Hostname of the server socket.
            port (int): Port to open the server socket on.
        """
        self.server = Server(hostname, port)
        self.console = console

    def get_socket_input(self) -> list[str]:
        """Receives input via the socket.

        Raises:
            Server.ConnectionBrokenException: If the socket connection is broken.

        Returns:
            list: A list containing a command and its arguments.
        """

        instruction = self.server.receive_line()
        self.server.send_line("200/OK")
        return instruction.split(" ")

    async def start(self):
        """|coro| Starts the CompanionConsole. Awaits a connection.

        Once connected, will receive commands over the socket and send them to
        the Console to be executed.
        """
        while self.console.online:
            _log.debug("TCP Socket Open...")
            try:
                await self.server.connect()
                _log.info("Companion Connected!")
                try:
                    await self.console.start(self.get_socket_input)
                except Server.ConnectionBrokenException:
                    _log.info("Companion Disconnected!")
            except OSError:
                _log.debug("TCP Socket waiting for connection was interupted.")

    def stop(self):
        """Stops the CompanionConsole by disconnecting the socket it is connected to."""

        self.server.disconnect()
