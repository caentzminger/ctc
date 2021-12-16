import asyncio
import typing

from ctc import directory
from ctc import spec
from ctc.toolbox import async_utils
from ctc.toolbox import nested_utils

from . import coracle_spec
from . import coracle_deposits
from . import coracle_balances


#
# # fei deposits
#


async def async_get_fei_deposit_balances(
    block: spec.BlockNumberReference = 'latest',
    provider: spec.ProviderSpec = None,
    normalize: bool = True,
) -> dict[spec.ContractAddress, typing.Union[int, float]]:

    fei_deposits = await coracle_deposits.async_get_token_deposits(
        token=directory.token_addresses['FEI'],
        block=block,
        provider=provider,
    )

    fei_balances = await coracle_balances.async_get_deposits_balances(
        deposits=fei_deposits,
        block=block,
        provider=provider,
    )


    result: typing.Union[list[int], list[float]]
    if normalize:
        result = [balance / 1e18 for balance in fei_balances]
    else:
        result = fei_balances

    return dict(zip(fei_deposits, result))


async def async_get_fei_deposit_balances_by_block(
    blocks: typing.Sequence[spec.BlockNumberReference],
    provider: spec.ProviderSpec = None,
) -> dict[spec.ContractAddress, list[typing.Union[int, float]]]:

    coroutines = [
        async_get_fei_deposit_balances(block=block, provider=provider)
        for block in blocks
    ]
    results = await async_utils.gather_coroutines(*coroutines)
    return nested_utils.list_of_dicts_to_dict_of_lists(results)


#
# # fei platforms
#


def fei_deposits_to_deployments(
    deposit_balances: dict[str, int]
) -> dict[str, int]:

    deployment_balances: dict[str, int] = {}
    for deposit, value in deposit_balances.items():

        if deposit in coracle_spec.deposit_metadata:
            deployment = coracle_spec.deposit_metadata[deposit]['platform']
        else:
            deployment = 'Other'

        deployment_balances.setdefault(deployment, 0)
        deployment_balances[deployment] += value

    return deployment_balances


def fei_deposits_to_deployments_by_block(
    deposit_balances_by_block: dict[str, list[int]]
) -> dict[str, list[int]]:

    deployment_balances_by_block: dict[str, list[int]] = {}

    for deposit, value in deposit_balances_by_block.items():

        if deposit in coracle_spec.deposit_metadata:
            deployment = coracle_spec.deposit_metadata[deposit]['platform']
        else:
            deployment = 'Other'

        n_blocks = len(value)
        empty = [0 for i in range(n_blocks)]
        deployment_balances_by_block.setdefault(deployment, empty)
        deployment_balances_by_block[deployment] = [
            lhs + rhs
            for lhs, rhs in zip(value, deployment_balances_by_block[deployment])
        ]

    return deployment_balances_by_block
