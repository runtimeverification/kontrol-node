from __future__ import annotations

import threading
import time
import sys
from typing import TYPE_CHECKING

import pytest

from kontrol_node.cli import VMOptions
from kontrol_node.rpc import StatefulKJsonRpcServer

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Final

SERVER_HOST: Final = 'localhost'


@pytest.fixture
def server() -> Iterator[StatefulKJsonRpcServer]:
    """Fixture to start a JSON-RPC server instance on a dynamically assigned port.

    This fixture sets up a new `StatefulKJsonRpcServer` instance for each test function, running it on a
    dynamically allocated port to avoid conflicts. The server is run in a separate thread to allow the
    test to interact with it.

    :yield: A `StatefulKJsonRpcServer` instance.
    """
    sys.setrecursionlimit(15000000)

    server = StatefulKJsonRpcServer(
        VMOptions({'definition_dir': None, 'port': 0, 'host': SERVER_HOST, 'steps_tracing': True})
    )

    server_thread = threading.Thread(target=server.serve)
    server_thread.start()

    time.sleep(2)
    yield server
    server.shutdown()
    server_thread.join()
