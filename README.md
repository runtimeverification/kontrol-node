# kontrol-node


## Build from source

#### K Framework

You need to install the [K Framework] on your system, see the instructions there.
The fastest way is via the [kup package manager], with which you can do to get the correct version of K:

```sh
kup install k.openssl.secp256k1 --version v$(cat deps/k_release)
```

#### Build using the virtual environment

Prerequsites: `python >= 3.10`, [`uv`](https://docs.astral.sh/uv/).

In order to build `kontrol-node`, you need to build these specific targets:
```sh
uv run kdist --verbose build -j2 kontrol-node.simbolik
```

To change the default compiler:
```sh
CXX=clang++-14 uv run kdist --verbose build -j2 kontrol-node.simbolik
```

On Apple Silicon:
```sh
APPLE_SILICON=true uv run kdist --verbose build -j2 kontrol-node.simbolik
```

Targets can be cleaned with:
```sh
uv run kdist clean
```

For more information, refer to `kdist --help`.

## For Developers

Use `make` to run common tasks (see the [Makefile](Makefile) for a complete list of available targets).

* `make build`: Build wheel
* `make check`: Check code style
* `make format`: Format code
* `make test-unit`: Run unit tests
* `make test-integration`: Run integration tests

[K Framework]: <https://kframework.org>
[kup package manager]: <https://github.com/runtimeverification/kup>
