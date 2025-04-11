# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import asyncio
import logging
import sys

import grpc
from aiohttp import web
from grpc_interfaces.model_registration.pb.service_pb2_grpc import add_ModelRegistrationServicer_to_server

from service.config import GRPC_SERVICE_PORT
from service.model_registration import ModelRegistration

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


async def healthz_handler(request):  # noqa: ANN001, ANN201, ARG001
    """Starts a kubernetes health service"""
    return web.Response(text="OK")


async def serve():  # noqa: ANN201
    """Starts Model Registartion service"""
    app = web.Application()
    app.router.add_get("/healthz", healthz_handler)

    server = grpc.aio.server()
    add_ModelRegistrationServicer_to_server(ModelRegistration(), server)
    server.add_insecure_port(f"[::]:{GRPC_SERVICE_PORT}")
    logging.info("ModelRegistration Service started.")
    await server.start()

    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)  # noqa: S104
    await site.start()

    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
