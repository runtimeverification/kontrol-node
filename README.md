# kontrol-node


## Build from source

#### K Framework

You need to install the [K Framework] on your system, see the instructions there.
The fastest way is via the [kup package manager], with which you can do to get the correct version of K:

```sh
kup install k.openssl.secp256k1 --version v$(cat deps/k_release)
```

```bash
poetry install

poetry run kdist clean

CXX=clang++-14 poetry run --no-cache kdist --verbose build -j8 kontrol-node.simbolik
```

#### Poetry dependencies

First you need to set up all the dependencies of the virtual environment using Poetry with the prerequisites `python 3.8.*`, `pip >= 20.0.2`, `poetry >= 1.3.2`:
```sh
poetry install
```

#### Build using the virtual environment

In order to build `kontrol-node`, you need to build these specific targets:
```sh
poetry run --no-cache kdist --verbose build -j2 kontrol-node.simbolik
```

To change the default compiler:
```sh
CXX=clang++-14 poetry run --no-cache kdist --verbose build -j2 kontrol-node.simbolik
```

On Apple Silicon:
```sh
APPLE_SILICON=true poetry run --no-cache kdist --verbose build -j2 kontrol-node.simbolik
```

Targets can be cleaned with:
```sh
poetry run kdist clean
```

For more information, refer to `kdist --help`.

## For Developers

Use `make` to run common tasks (see the [Makefile](Makefile) for a complete list of available targets).

* `make build`: Build wheel
* `make check`: Check code style
* `make format`: Format code
* `make test-unit`: Run unit tests
* `make test-integration`: Run integration tests

For interactive use, spawn a shell with `poetry shell` (after `poetry install`), then run an interpreter.

[K Framework]: <https://kframework.org>
[kup package manager]: <https://github.com/runtimeverification/kup>
