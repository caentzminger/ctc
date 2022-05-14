from __future__ import annotations

from ctc import spec

from .. import db_connect
from .. import db_crud


async def async_query_contract_abi(
    address: spec.Address,
    network: spec.NetworkReference,
) -> spec.ContractABI | None:
    engine = db_connect.create_engine(
        datatype='contract_abi',
        network=network,
    )
    if engine is None:
        return None
    with engine.connect() as conn:
        return await db_crud.async_select_contract_abi(
            conn=conn,
            address=address,
            network=network,
        )