# ⛓️ Kontrol Node

**A local Ethereum testnet node powered by [KEVM](https://github.com/runtimeverification/evm-semantics), the K formal semantics of the EVM.**

[![Install](https://img.shields.io/badge/install-kup-blue)](https://kframework.org/install)
[![Discord](https://img.shields.io/badge/discord-join-7289da)](https://discord.gg/CurfmXNtbN)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-green)](LICENSE)

[Installation](#installation) • [Usage](#usage) • [JSON-RPC API](#json-rpc-api) • [Contribute](#for-developers)

---

## 🌟 Overview

`kontrol-node` serves the standard
[Ethereum JSON-RPC](https://ethereum.org/en/developers/docs/apis/json-rpc/) API on chain ID `31337`
with the same ten pre-funded accounts as Anvil and Hardhat, so existing SDKs, wallets, and
Foundry-based tooling work against it unchanged — just point them at `localhost`.

What differs is what happens *inside* a transaction. Execution is by KEVM, the same executable EVM
specification [Kontrol](https://github.com/runtimeverification/kontrol) uses for formal
verification, which buys two things an ordinary dev node cannot offer:

- **Opcode-level traces with full state deltas.** `debug_traceTransaction` returns geth-style
  `structLogs`, but each step also carries the storage, balance, nonce and code changes, the memory,
  calldata, returndata and program deltas, and the full call context. That is enough to replay an
  execution step by step — which is what makes it a debugger backend, and the engine behind
  [Simbolik](https://simbolik.runtimeverification.com/), Runtime Verification's Solidity debugger.
- **Behavior you can read.** RPC dispatch, block production and the EVM itself are all K rewrite
  rules in [`src/kontrol_node/kdist/`](src/kontrol_node/kdist/) — the specification *is* the
  implementation.

The trade-off is speed: expect seconds per transaction. This is a node for debugging individual
transactions, not for load testing.

## 🚀 Quick Start

### Installation

`kontrol-node` is distributed through [`kup`](https://github.com/runtimeverification/kup), Runtime
Verification's Nix-based package manager. It pulls prebuilt binaries — including the matching K
Framework and compiled semantics — from RV's binary cache, so there is nothing to compile.

```bash
# 1. Install the kup package manager (one time)
bash <(curl https://kframework.org/install)

# 2. Install kontrol-node
kup install kontrol-node

# 3. Verify the installation
kontrol-node version
```

Upgrade with `kup update kontrol-node`, or see [Build from source](#build-from-source).

---

### Usage

#### Start the node

`kontrol-node run` starts the JSON-RPC server:

```
usage: kontrol-node run [-h] [--verbose] [--debug] [--config-file CONFIG_FILE]
                        [--config-profile CONFIG_PROFILE] [--host ADDR]
                        [--port PORT]

options:
  -h, --help            show this help message and exit
  --verbose, -v         Verbose output.
  --debug               Debug output.
  --config-file CONFIG_FILE
                        Path to Pyk config file.
  --config-profile CONFIG_PROFILE
                        Config profile to be used.
  --host ADDR           host address        (default: 127.0.0.1)
  --port PORT           port number         (default: 8081)
```

```bash
kontrol-node run                          # serve on 127.0.0.1:8081
kontrol-node run --port 8545              # use the conventional Ethereum port
kontrol-node run --host 0.0.0.0           # accept connections from outside localhost
```

Chain state lives in a fresh `io_dir*` directory under the working directory and is removed on exit,
so **every run starts from genesis**. Requests are handled one at a time.

#### Deploy and call a contract

There is no mempool: `eth_sendTransaction` executes the transaction synchronously, mines a block for
it, and returns its hash, so the receipt is ready as soon as the call returns. Transactions are
submitted **unsigned** — name an unlocked account in `from` and the node signs for you.

The walkthrough below deploys this contract and increments it:

```solidity
contract Counter {
    uint256 public count;  // slot 0
    function increment() public { count += 1; }
}
```

```bash
# Is the node alive?
curl -s http://127.0.0.1:8081 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}'
# => {"jsonrpc":"2.0","id":1,"result":31337}

# 1. Deploy Counter — `data` is the contract's init code, `to` is omitted
curl -s http://127.0.0.1:8081 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"eth_sendTransaction","params":[{
        "from":"0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "gas":"0x1c9c37f","gasPrice":"0x1d1a94a2000","value":"0",
        "data":"0x6080604052348015600f57600080fd5b5060f78061001e6000396000f3fe6080604052348015600f57600080fd5b5060043610603c5760003560e01c80633fb5c1cb1460415780638381f58a146053578063d09de08a14606d575b600080fd5b6051604c3660046083565b600055565b005b605b60005481565b60405190815260200160405180910390f35b6051600080549080607c83609b565b9190505550565b600060208284031215609457600080fd5b5035919050565b60006001820160ba57634e487b7160e01b600052601160045260246000fd5b506001019056fea2646970667358221220380554e236eca25e41ce3f83305e720d4442aaad4e06b3f2ca8b7900b823776c64736f6c634300081a0033"}]}'
# => {"jsonrpc":"2.0","id":2,"result":"0xa2a48bf94c47073aa235c34e3dfe9bd9687e7b6a6cce28a2380ed48138f51680"}

# 2. Read the receipt to find the deployed address
curl -s http://127.0.0.1:8081 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":3,"method":"eth_getTransactionReceipt",
       "params":["0xa2a48bf94c47073aa235c34e3dfe9bd9687e7b6a6cce28a2380ed48138f51680"]}'
# => {..."contractAddress":"0x5fbdb2315678afecb367f032d93f642f64180aa3","gasUsed":"0x1a0e1","status":"0x1"...}

# 3. Call increment() — selector 0xd09de08a
curl -s http://127.0.0.1:8081 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":4,"method":"eth_sendTransaction","params":[{
        "from":"0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "to":"0x5FbDB2315678afecb367f032d93F642f64180aa3",
        "gas":"0x1c9c37f","gasPrice":"0x1d1a94a2000","value":"0",
        "data":"0xd09de08a"}]}'
# => {"jsonrpc":"2.0","id":4,"result":"0x8f2c14205d39e138de7b5133c260405ff4fb68f2ee7212ee521986956867bd81"}

# 4. Confirm `count` went to 1 by reading storage slot 0
curl -s http://127.0.0.1:8081 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":5,"method":"eth_getStorageAt",
       "params":["0x5FbDB2315678afecb367f032d93F642f64180aa3","0x0","latest"]}'
# => {"jsonrpc":"2.0","id":5,"result":"0x1"}
```

Since every run starts from genesis, the deployed address and both transaction hashes are the same
each time — the commands above can be pasted verbatim.

Requests can be **batched**: post an array of request objects, get an array of responses in order.

```bash
curl -s http://127.0.0.1:8081 -H 'Content-Type: application/json' \
  -d '[{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]},
       {"jsonrpc":"2.0","id":2,"method":"eth_getTransactionCount","params":["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266","latest"]}]'
# => [{"jsonrpc":"2.0","id":1,"result":31337},
#     {"jsonrpc":"2.0","id":2,"result":"0x2"}]
```

#### Trace a transaction

`debug_traceTransaction` returns the record of every opcode a mined transaction executed, keyed by
the hash `eth_sendTransaction` gave you — so tracing is two requests: send, then trace. The second
parameter is geth's tracer-options object, currently ignored; pass `{}`.

```bash
curl -s http://127.0.0.1:8081 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":6,"method":"debug_traceTransaction",
       "params":["0x8f2c14205d39e138de7b5133c260405ff4fb68f2ee7212ee521986956867bd81",{}]}'
```

The result is geth-shaped: `failed`, `gas`, `returnValue`, and one `structLogs` entry per opcode.
The `increment()` call above produces 67:

```jsonc
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "failed": false,
    "gas": 43404,
    "returnValue": "",
    "structLogs": [ /* 67 entries, one per opcode */ ]
  }
}
```

Each entry snapshots the machine plus the state *changed by the previous step*. Here is the entry
right after the `SSTORE` that writes `count = 1`, showing that write in `storageChanges`:

```jsonc
{
  "op": "POP",                   // opcode about to execute
  "pc": 129,                     // program counter
  "depth": 1,                    // call depth
  "gas": 29956606,               // gas remaining
  "gasCost": 2000000000000,      // cost of this step
  "stack": ["0xd09de08a", "0x51", "0x0"],   // top of stack last
  "statusCode": "empty",         // KEVM status code; "empty" while still running

  // State deltas — what the previous step changed. `{}` means "nothing changed".
  "storageChanges": {"0x5fbdb2315678afecb367f032d93f642f64180aa3": {"0x0": "0x1"}},
  "balanceChanges": {},
  "nonceChanges": {},
  "deployedCodeChanges": {},
  "initCodeChanges": {},

  // Byte-buffer deltas — `null` means "unchanged since the previous entry".
  "memoryChange": null,
  "callDataChange": null,
  "returnDataChange": null,
  "programChange": null,

  // Call context. Addresses in this group are decimal integers, not hex strings.
  "msgSender":     1390849295786071768276380950238675083608645509734,
  "txOrigin":      1390849295786071768276380950238675083608645509734,
  "targetAddress":  546584486846459126461364135121053344201067465379,
  "codeAddress":    546584486846459126461364135121053344201067465379,
  "msgValue": 0,
  "isInitCode": false,

  // Block context
  "blockNumber": 2,
  "blockTimestamp": 1768610547,
  "coinbase": 0,
  "difficulty": 0
}
```

Two conventions to know before writing a consumer:

- **Deltas, not snapshots.** The `*Changes` maps and `*Change` buffers report what the *previous*
  step changed, so a write appears on the entry *after* the `SSTORE`. Maps use `{}` for "unchanged",
  buffers use `null` ("reuse the last value seen"). Replaying the deltas in order reconstructs the
  full state at every step.
- **Addresses are encoded inconsistently.** `*Changes` keys are hex strings, but `msgSender`,
  `txOrigin`, `targetAddress`, `codeAddress` and `coinbase` are decimal integers — convert before
  comparing.

Reverting transactions are traced too: `failed` is `true` and the `structLogs` still cover the
opcodes that ran.

---

## JSON-RPC API

The implemented subset covers deploying, calling, inspecting and debugging contracts. All requests
are `POST`ed to the server root.

| Method | Parameters | Notes |
|---|---|---|
| `eth_chainId` | — | Returns `31337` as a JSON number, not a hex quantity |
| `eth_sendTransaction` | `[tx]` | Unsigned tx object (`from`, `to`, `gas`, `gasPrice`, `value`, `data`); executes synchronously, mines a block, returns the tx hash |
| `eth_getTransactionByHash` | `[hash]` | |
| `eth_getTransactionReceipt` | `[hash]` | Includes `contractAddress` for deployments |
| `eth_getTransactionCount` | `[address, block]` | |
| `eth_getBalance` | `[address, block]` | |
| `eth_getCode` | `[address, block]` | |
| `eth_getStorageAt` | `[address, slot, block]` | |
| `eth_getBlockByNumber` | `[block, hydrated]` | |
| `eth_getBlockByHash` | `[hash, hydrated]` | |
| `anvil_dumpState` | `[""]` | Full state snapshot: latest block header, every account's balance, nonce, code and storage, the block history, and all transaction receipts |
| `anvil_setBalance` | `[address, balance]` | |
| `debug_traceTransaction` | `[hash, options]` | Opcode-level trace; `options` is accepted and ignored |

`block` takes a hex number or the tags `"earliest"`, `"latest"`, `"safe"`, `"finalized"`,
`"pending"` — the middle two resolve to latest, since every block here is final. Errors follow
JSON-RPC: `-32601` unknown method, `-32700` malformed JSON, `-32600` malformed request, `-32603` a
request the semantics cannot process.

### Pre-funded accounts

Ten accounts are unlocked and funded with 10 000 ETH each, derived from the mnemonic
`test test test test test test test test test test test junk` — the same accounts, with the same
well-known keys, that Anvil and Hardhat use.

| Address | Private key |
|---|---|
| `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` | `0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80` |
| `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` | `0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d` |
| `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` | `0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a` |
| `0x90F79bf6EB2c4f870365E785982E1f101E93b906` | `0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6` |
| `0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65` | `0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a` |
| `0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc` | `0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba` |
| `0x976EA74026E726554dB657fA54763abd0C3a0aa9` | `0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e` |
| `0x14dC79964da2C08b23698B3D3cc7Ca32193d9955` | `0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356` |
| `0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f` | `0xdbda1821b80551c9d65939329250298aa3472ba22feea921c0cf5d620ea67b97` |
| `0xa0Ee7A142d267C1f36714E4a8F75612F20a79720` | `0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6` |

> These keys are public. Never send real funds to these addresses.

The first account is the default sender when a transaction omits `from`. Foundry's deterministic
CREATE2 deployer is pre-deployed at `0x4e59b44847b379578588920ca78fbf26c0b4956c`.

### Chain configuration and behavior

- **Chain ID** `31337`, **EVM version** Prague, **block gas limit** `30_000_000`, gas metering on.
- **One block per transaction**, mined automatically; no mempool, no separate mining step.
- **EIP-170 code size checks are disabled**, so oversized contracts deploy as-is.
- **Foundry cheatcodes** are recognized at the usual `vm` address
  (`0x7109709ECfa91a80626fF3989D68f67F5b1DD12D`). A cheatcode Kontrol does not implement reverts the
  transaction instead of hanging the node, and the revert shows up in the trace.

### Current limitations

- **State is not persistent** — each run is a fresh chain, with no flag to keep or reload one.
- **No `eth_sendRawTransaction`**, so a client that signs locally cannot submit here.
- **Block `transactions` arrays are always empty** in `eth_getBlockByNumber` and
  `eth_getBlockByHash`, for both `hydrated` values; read transactions by hash instead.
- **`eth_chainId` returns a JSON number** (`31337`) where the spec requires a hex quantity
  (`"0x7a69"`); a strict client may reject it.
- **No event-log or filter methods**, no `eth_call`, no `eth_estimateGas`, no WebSocket transport.
- **Throughput is low** — every request runs the K interpreter over the whole semantics.

---

## For Developers

Prerequisites: `python >= 3.10`, [`uv`](https://docs.astral.sh/uv/), and the K Framework. Integration
and end-to-end tests also need [Foundry](https://getfoundry.sh/), for `forge` and `anvil`.

### Build from source

Install the pinned K Framework version, then compile the semantics:

```bash
# 1. Install the matching K Framework via kup
kup install k.openssl.secp256k1 --version v$(cat deps/k_release)

# 2. Compile the K semantics (first run takes a while)
make kdist-build

# 3. Run the node from the source checkout
uv run kontrol-node run
```

`make kdist-build` wraps `uv run kdist build kontrol-node.*`. To drive `kdist` directly:

```bash
# Choose a different compiler
CXX=clang++-15 uv run kdist --verbose build -j2 kontrol-node.simbolik -f

# Apple Silicon
APPLE_SILICON=true uv run kdist --verbose build -j2 kontrol-node.simbolik

# Clean the build
uv run kdist clean
```

See `kdist --help` for all options. A Nix flake is also provided: `nix develop` gives a shell with K
and every build dependency, `nix build` builds the package.

To build and install the wheel:

```bash
make build
pip install dist/*.whl
```

### Common tasks

Driven by `make` (see the [Makefile](Makefile) for the full list):

| Target | Description |
|---|---|
| `make kdist-build` | Compile the K semantics (required before integration, e2e, and any real use) |
| `make build` | Build the wheel |
| `make test-unit` | Run unit tests (fast; no semantics needed) |
| `make test-integration` | Replay recorded JSON-RPC requests, singly and batched, against expected responses — and against real Anvil |
| `make test-e2e` | Compile Solidity with `forge`, deploy it, and drive it over JSON-RPC |
| `make test` | Run the full test suite |
| `make cov` | Run tests with a coverage report |
| `make check` | Run all style and type checks (flake8, mypy, autoflake, isort, black) |
| `make format` | Auto-format the codebase |

The integration suite is golden-file based: each case in
[`src/tests/integration/test-data/`](src/tests/integration/test-data/) pairs an `.in.json` request
with an `.expected.json` response. Regenerate expectations rather than hand-editing them:

```bash
make test-integration TEST_ARGS=--update-expected-output
```

That suite also includes `test_anvil_compatibility`, which sends every recorded request to both
`kontrol-node` and a real `anvil` and asserts the responses match — run it before changing any
response shape.

### Repository layout

| Path | Contents |
|---|---|
| [`src/kontrol_node/rpc.py`](src/kontrol_node/rpc.py) | The HTTP server and the interpreter bridge |
| [`src/kontrol_node/cli.py`](src/kontrol_node/cli.py) | Command-line interface |
| [`src/kontrol_node/genesis.json`](src/kontrol_node/genesis.json) | Genesis block and pre-funded accounts |
| [`src/kontrol_node/kdist/node.md`](src/kontrol_node/kdist/node.md) | K semantics: JSON-RPC dispatch, block production, state snapshots |
| [`src/kontrol_node/kdist/trace.md`](src/kontrol_node/kdist/trace.md) | K semantics: opcode trace collection |
| [`src/kontrol_node/kdist/trace-json.md`](src/kontrol_node/kdist/trace-json.md) | K semantics: JSON encoding of traces |
| [`src/tests/`](src/tests/) | Unit, integration, and end-to-end tests |

### How it works

The Python process is a thin server; all execution lives in the semantics. It creates an I/O
directory holding the genesis state, then for each request:

1. writes the request body to `request.json`,
2. runs the compiled K definition, which loads the latest state snapshot, dispatches the method,
   executes any transaction, and writes `response.json` plus the new block snapshot, receipt and
   trace,
3. streams `response.json` back to the client.

Requests are therefore serialized, and the K interpreter — not Python — defines what each method
means. Adding an RPC method means adding rules to
[`node.md`](src/kontrol_node/kdist/node.md), not Python code.

---

## About

`kontrol-node` is developed by [Runtime Verification](https://runtimeverification.com/), building on
[Kontrol](https://github.com/runtimeverification/kontrol),
[KEVM](https://github.com/runtimeverification/evm-semantics) and the
[K Framework](https://github.com/runtimeverification/k). It is the execution engine behind
[Simbolik](https://simbolik.runtimeverification.com/), RV's Solidity debugger.

Licensed under the [BSD 3-Clause License](LICENSE). Questions and contributions welcome — find us on
[Discord](https://discord.gg/CurfmXNtbN) or open an issue.
