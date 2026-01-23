from __future__ import annotations

import sys
import threading
import time
from typing import TYPE_CHECKING

import pytest

from kontrol_node.options import VMOptions
from kontrol_node.rpc import KontrolNodeServer

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Final

SERVER_HOST: Final = 'localhost'


@pytest.fixture
def server() -> Iterator[KontrolNodeServer]:
    """Fixture to start a JSON-RPC server instance on a dynamically assigned port.

    This fixture sets up a new `StatefulKJsonRpcServer` instance for each test function, running it on a
    dynamically allocated port to avoid conflicts. The server is run in a separate thread to allow the
    test to interact with it.

    :yield: A `StatefulKJsonRpcServer` instance.
    """
    sys.setrecursionlimit(15000000)

    server = KontrolNodeServer(VMOptions({'host': SERVER_HOST, 'port': 0}))

    server_thread = threading.Thread(target=server.serve)
    server_thread.start()

    time.sleep(2)
    yield server
    server.shutdown()
    server_thread.join()
