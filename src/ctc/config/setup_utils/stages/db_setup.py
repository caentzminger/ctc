from __future__ import annotations

import os
import typing

import toolcli

from ctc import spec
from ... import config_defaults


def setup_dbs(
    styles: typing.Mapping[str, str],
    data_root: str,
) -> spec.PartialConfigSpec:

    print()
    print()
    toolcli.print('## Database Setup', style=styles['header'])
    print()
    print('ctc stores its collected chain data in an sql database')
    print()

    db_configs = config_defaults.get_default_db_configs(data_root)

    # create db
    print()
    for db_config in db_configs.values():
        if 'path' in db_config:
            db_path = db_config['path']
            db_dirpath = os.path.dirname(db_path)
            os.makedirs(db_dirpath, exist_ok=True)

        if not os.path.isfile(db_path):
            print('Creating database at path', db_path)
        else:
            print('Existing database detected at path', db_path)

    # create tables
    pass

    return {'db_configs': db_configs}


async def async_populate_db_tables(styles: typing.Mapping[str, str]) -> None:
    from ctc import db
    from ctc.protocols import chainlink_utils

    print()
    print()
    toolcli.print('## Populating Database', style=styles['header'])

    # populate data: erc20s
    print()
    print('Populating database with metadata of common ERC20 tokens...')
    print()
    await db.async_intake_default_tokens(network='mainnet')

    # populate data: chainlink
    print()
    print('Populating database with Chainlink oracle feeds...')
    print()
    await chainlink_utils.async_import_networks_to_db()
