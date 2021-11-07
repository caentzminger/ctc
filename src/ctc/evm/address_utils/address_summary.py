from .. import rpc_utils
from .. import contract_abi_utils
from . import address_data


def print_address_summary(address, verbose=0, max_width=80):
    """

    TODO (with more data)
    - transactions
    - transfers
    """

    eth_balance = rpc_utils.eth_get_balance(address)
    transaction_count = rpc_utils.eth_get_transaction_count(address)

    # contract data
    code = rpc_utils.eth_get_code(address)
    is_contract = code != '0x'
    if is_contract:
        address_type = 'contract'
    else:
        address_type = 'EOA'

    title = 'Address ' + address.lower()
    print(title)
    print('─' * len(title))
    print('- checksum:', address_data.get_address_checksum(address))
    print('- address type:', address_type)
    print('- ETH balance:', eth_balance)
    print('- transaction count:', transaction_count)
    print('- first transaction:')

    if is_contract:
        print()
        print()

        contract_abi = contract_abi_utils.get_contract_abi(
            contract_address=address
        )
        df = contract_abi_utils.contract_abi_to_dataframe(
            contract_abi=contract_abi, human_readable=False
        )

        functions = df[df['type'] == 'function']
        functions = functions.drop(columns=['type', 'anonymous'])

        print('Contract ABI Functions')
        print('──────────────────────')
        for i, (f, function) in enumerate(functions.iterrows()):

            if len(function['outputs']) == 0:
                output_str = '[none]'
            else:
                output_str = [
                    item['type'] + ' ' + item['name']
                    for item in function['outputs']
                ]
                output_str = ', '.join(output_str)
                if len(function['outputs']) > 1:
                    output_str = '(' + output_str + ')'

            if not verbose:
                signature = contract_abi_utils.get_function_signature(
                    function_abi=function, include_names=True
                )
            else:
                signature = function['name'] + '()'
            if verbose:
                text = signature + ' --> ' + str(output_str)
            else:
                text = str(i + 1) + '. ' + signature + ' --> ' + str(output_str)

            if len(text) > max_width:
                text = text[: max_width - 3] + '...'

            print(text)
            if verbose:
                indent = ''
                if verbose > 1:
                    indent = '    '
                    print(indent + '- mutability:', function['stateMutability'])
                    print(indent + '- inputs:')
                if len(function['inputs']) == 0:
                    print(indent + '    [no inputs]')
                for i, item in enumerate(function['inputs']):
                    print(
                        indent + '    ' + str(i + 1) + '.',
                        item['type'],
                        item['name'],
                    )
                print()

        events = df[df['type'] == 'event']
        print()
        print('Contract ABI Events')
        print('───────────────────')
        if len(events) == 0:
            print('[none]')
        for i, (e, event) in enumerate(events.iterrows()):
            event_hash = contract_abi_utils.get_event_hash(event_abi=event)
            signature = contract_abi_utils.get_event_signature(event_abi=event)
            line = str(i + 1) + '. ' + signature
            if len(line) > max_width:
                line = line[:max_width - 3] + '...'
            print(line)
            if verbose:
                print('  ', event_hash)
                if i + 1 != len(events):
                    print()
