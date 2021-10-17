import toolcache
import web3

from ctc import evm
from . import instance_utils


@toolcache.cache('memory')
def get_web3_contract(
    contract=None,
    contract_address=None,
    contract_name=None,
    project=None,
    contract_abi=None,
    web3_instance=None,
    provider=None,
):
    if web3_instance is None:
        web3_instance = instance_utils.create_web3_instance(provider=provider)

    if isinstance(contract, web3.contract.Contract):
        return contract
    elif isinstance(contract, str):
        if evm.is_address_str(contract):
            contract_address = contract
        else:
            contract_name = contract
    elif contract is not None:
        raise Exception('unknown contract type')

    if contract_abi is None:
        contract_abi = evm.load_named_contract_abi(
            contract_address=contract_address,
            contract_name=contract_name,
            project=project,
        )

    if contract_address is None:
        if contract_name is not None:
            pass
        else:
            raise Exception()

    contract_address = web3.Web3.toChecksumAddress(contract_address)
    return web3_instance.eth.contract(contract_address, abi=contract_abi)


def call_web3_contract(
    contract, function, abi=None, args=None, block=None, **contract_kwargs
):
    if args is None:
        args = {}
    if block is None:
        block = 'latest'

    contract = get_web3_contract(
        contract=contract, contract_abi=abi, **contract_kwargs
    )

    return contract.functions[function](*args).call({}, block)

