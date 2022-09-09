from __future__ import annotations

from ctc import binary
from ctc import spec
from . import transaction_serialize


def get_unsigned_transaction_hash(
    transaction: spec.TransactionData,
    *,
    chain_id: int | None = None,
) -> spec.Data:

    serialized = transaction_serialize.serialize_unsigned_transaction(
        transaction,
        chain_id=chain_id,
    )
    return binary.keccak(serialized)


def get_signed_transaction_hash(transaction: spec.TransactionData) -> spec.Data:
    serialized = transaction_serialize.serialize_signed_transaction(transaction)
    return binary.keccak(serialized)