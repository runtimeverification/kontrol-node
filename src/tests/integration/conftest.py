from __future__ import annotations

import socket
import threading
import time
from typing import TYPE_CHECKING

import pytest
from pyk.rpc.rpc import ServeRpcOptions

from kontrol_node.rpc import StatefulKJsonRpcServer

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Final

SERVER_HOST: Final = 'localhost'


def get_free_port() -> int:
    """Finds an available port on the system by temporarily binding to a free port and returning its number.

    :return: port
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='function')
def server_instance() -> Iterator[tuple[StatefulKJsonRpcServer, int]]:
    """Fixture to start a JSON-RPC server instance on a dynamically assigned port.

    This fixture sets up a new `StatefulKJsonRpcServer` instance for each test function, running it on a
    dynamically allocated port to avoid conflicts. The server is run in a separate thread to allow the
    test to interact with it.

    :yield: A tuple containing the server instance and the port number it is running on.
    """

    port = get_free_port()
    server = StatefulKJsonRpcServer(ServeRpcOptions({'definition_dir': None, 'port': port, 'host': SERVER_HOST}))

    server_thread = threading.Thread(target=server.serve)
    server_thread.start()

    time.sleep(2)

    yield (server, port)
    server.shutdown()
    server_thread.join()
