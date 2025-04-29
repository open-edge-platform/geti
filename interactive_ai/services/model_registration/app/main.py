# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
