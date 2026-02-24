from __future__ import annotations

import re
import subprocess
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
def server() -> Iterator[str]:
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
    yield f"http://{SERVER_HOST}:{server.port()}"
    server.shutdown()
    server_thread.join()

@pytest.fixture
def anvil() -> Iterator[str]:
    """Fixture to start an Anvil instance on a dynamically assigned port.

    This fixture starts an Anvil instance for each test function, running it on a dynamically allocated
    port to avoid conflicts. The fixture yields the host and port information for the Anvil instance.

    :yield: A tuple containing the host and port of the Anvil instance.
    """
    cmd = ('anvil', '--port', '0', '--steps-tracing')
    host_pattern = r'Listening on (.+):(\d+)'
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    time.sleep(2)
    assert process.stdout is not None
    for line in process.stdout:
        match = re.search(host_pattern, line)
        if match:
            host, port = match.groups()
            break
    else:
        process.terminate()
        raise RuntimeError("Failed to start Anvil and retrieve host/port information.")
    
    yield f"http://{host}:{port}"
    process.terminate()