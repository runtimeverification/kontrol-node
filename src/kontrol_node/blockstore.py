from __future__ import annotations


class BlockStore:
    """
    A class to store and manage blockchain blocks, allowing access by block number or block hash.

    This class maintains internal dictionaries to provide O(1) access time for blocks
    using either their block number or block hash. Blocks are stored as dictionaries
    and must contain at least 'number' and 'hash' keys.

        :attr _blocks: Internal list where block information is stored.
        :attr _index_by_number: Internal mapping from block number to index.
        :attr _index_by_hash: Internal mapping from block hash to index.
    """

    def __init__(self) -> None:
        self._blocks: list[dict] = []
        self._index_by_number: dict[int, int] = {}
        self._index_by_hash: dict[int, int] = {}

    def add_block(self, block: dict) -> None:
        index = len(self._blocks)
        self._blocks.append(block)
        self._index_by_number[int(block['number'], 0)] = index
        self._index_by_hash[int(block['hash'], 0)] = index

    def get_block_by_number(self, number: int) -> dict | None:
        index = self._index_by_number.get(number)
        if index is not None:
            return self._blocks[index]
        return None

    def get_block_by_hash(self, hash: int) -> dict | None:
        index = self._index_by_hash.get(hash)
        if index is not None:
            return self._blocks[index]
        return None

    def get_latest_block(self) -> dict | None:
        if self._blocks:
            return self._blocks[-1]
        return None
