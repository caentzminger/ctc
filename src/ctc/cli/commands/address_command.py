import os

from ctc import evm


def get_command_spec():
    return {
        'f': address_command,
        'options': [
            {'name': 'address'},
            {'name': ['-v', '--verbose'], 'kwargs': {'action': 'store_true'}},
        ],
    }


def address_command(address, verbose, **kwargs):
    max_width = os.get_terminal_size().columns
    evm.print_address_summary(
        address=address, verbose=verbose, max_width=max_width
    )

