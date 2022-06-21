from __future__ import annotations

import math
import random
import typing

from ctc import config
from ctc import spec
from . import rpc_provider


_rpc_logger_state = {
    'logger_setup': False,
}


def setup_rpc_logger() -> None:
    import loguru

    if not _rpc_logger_state['logger_setup']:

        # get logging path
        rpc_log_path = config.get_rpc_requests_log_path()

        # enqueue makes logging non-blocking for async compatibility
        loguru.logger.remove()
        loguru.logger.add(
            rpc_log_path,
            enqueue=True,
            rotation='10 MB',
            format='{time} {message}',
        )

        _rpc_logger_state['logger_setup'] = True


def log_rpc_request(
    request: spec.RpcRequest, provider: spec.ProviderSpec
) -> None:
    try:
        import loguru
    except ImportError:
        import warnings

        warnings.warn(
            'to use logging must install loguru, use `pip install loguru`'
        )
        return

    setup_rpc_logger()

    if isinstance(request, dict):
        loguru.logger.info(
            'request  ' + request['method'] + ' id=' + str(request['id'])
        )
    elif isinstance(request, list):
        entries = '\n'.join(
            '    ' + subrequest['method'] + ' id=' + str(subrequest['id'])
            for subrequest in request
        )
        loguru.logger.info('bulk request\n' + entries)
    else:
        raise Exception('cannot log request, unknown request type')


def log_rpc_response(
    response: spec.RpcResponse,
    request: spec.RpcRequest,
    provider: spec.ProviderSpec,
) -> None:
    import loguru

    setup_rpc_logger()

    if isinstance(request, dict):
        loguru.logger.info(
            'response ' + request['method'] + ' id=' + str(request['id'])
        )
    elif isinstance(request, list):
        entries = '\n'.join(
            '    ' + subrequest['method'] + ' id=' + str(subrequest['id'])
            for subrequest in request
        )
        loguru.logger.info('bulk response\n' + entries)


def create(method: str, parameters: list[typing.Any]) -> spec.RpcRequest:
    return {
        'jsonrpc': '2.0',
        'method': method,
        'params': parameters,
        'id': random.randint(1, int(1e18)),
    }


async def async_send(
    request: spec.RpcRequest,
    provider: typing.Optional[spec.ProviderSpec] = None,
) -> spec.RpcResponse:
    full_provider = rpc_provider.get_provider(provider)

    try:
        logging_rpc_calls = config.get_log_rpc_calls()
    except Exception:
        logging_rpc_calls = False
    if logging_rpc_calls:
        log_rpc_request(request=request, provider=full_provider)

    if isinstance(request, dict):
        response = await async_send_raw(request=request, provider=full_provider)
        if 'result' not in response and 'error' in response:
            response = typing.cast(spec.RpcSingularResponseFailure, response)
            raise spec.RpcException(
                'RPC ERROR: ' + response['error']['message']
            )
        else:
            response = typing.cast(spec.RpcSingularResponseSuccess, response)
            output = response['result']

    elif isinstance(request, list):

        # chunk request
        request_chunks = chunk_request(request=request, provider=full_provider)

        import logging

        logger = logging.getLogger()
        logger.info(
            'chunking batch of '
            + str(len(request))
            + ' calls into '
            + str(len(request_chunks))
            + ' chunks'
        )

        # send request chunks
        coroutines = []
        for request_chunk in request_chunks:
            coroutine = async_send_raw(
                request=request_chunk,
                provider=full_provider,
            )
            coroutines.append(coroutine)

        import asyncio

        response_chunks = await asyncio.gather(*coroutines)

        # reorder chunks
        plural_response = reorder_response_chunks(response_chunks, request)

        output = [subresponse['result'] for subresponse in plural_response]

    else:

        raise Exception('unknown request type: ' + str(type(request)))

    if logging_rpc_calls:
        if isinstance(request, dict):
            log_rpc_response(
                response=response,
                request=request,
                provider=provider,
            )
        elif isinstance(request, list):
            log_rpc_response(
                response=plural_response,
                request=request,
                provider=provider,
            )

    return output


@typing.overload
async def async_send_raw(
    request: spec.RpcSingularRequest, provider: spec.Provider
) -> spec.RpcSingularResponseRaw:
    ...


@typing.overload
async def async_send_raw(
    request: spec.RpcPluralRequest, provider: spec.Provider
) -> spec.RpcPluralResponseRaw:
    ...


async def async_send_raw(
    request: spec.RpcRequest,
    provider: spec.Provider,
) -> spec.RpcResponseRaw:

    _log_request(request=request, provider=provider)

    if provider['protocol'] == 'http':
        from .rpc_backends import rpc_http_async

        return await rpc_http_async.async_send_http(
            request=request,
            provider=provider,
        )

    elif provider['protocol'] == 'wss':
        from .rpc_backends import rpc_websocket_async

        return await rpc_websocket_async.async_send_websocket(
            request=request,
            provider=provider,
        )

    else:
        raise Exception(
            'unknown provider protocol: ' + str(provider['protocol'])
        )


def _log_request(request: spec.RpcRequest, provider: spec.Provider) -> None:
    import logging

    logger = logging.getLogger()
    if isinstance(request, dict):
        logger.info('singular request: ' + request['method'])
    elif isinstance(request, list):
        methods = [subrequest['method'] for subrequest in request]
        logger.info(
            'plural request: '
            + str(len(request))
            + ' calls, '
            + str(set(methods))
        )
    else:
        raise Exception('unknown request type: ' + str(type(request)))


def reorder_response_chunks(
    response_chunks: list[spec.RpcPluralResponseRaw],
    request: spec.RpcPluralRequest,
) -> spec.RpcPluralResponse:

    responses_by_id = {
        response['id']: response
        for response_chunk in response_chunks
        for response in response_chunk
    }
    return [responses_by_id[subrequest['id']] for subrequest in request]


#
# # chunking
#


def chunk_request(
    request: spec.RpcPluralRequest, provider: spec.Provider
) -> list[spec.RpcPluralRequest]:

    if provider['chunk_size'] is not None:
        return chunk_request_by_size(request, provider['chunk_size'])
    else:
        return [request]


def chunk_request_by_size(
    request: spec.RpcPluralRequest, chunk_size: int
) -> list[spec.RpcPluralRequest]:

    n_chunks = math.ceil(len(request) / chunk_size)
    return [
        request[slice(c * chunk_size, (c + 1) * chunk_size)]
        for c in range(n_chunks)
    ]


def chunk_request_by_method(request: spec.RpcRequest) -> None:
    raise NotImplementedError()


def chunk_request_by_block_range(request: spec.RpcRequest) -> None:
    raise NotImplementedError()

