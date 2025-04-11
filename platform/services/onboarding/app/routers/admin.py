# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from datetime import date

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, model_validator
from typing_extensions import Self

from geti_logger_tools.logger_config import initialize_logger
from jwt_utils import OnboardingTokenService

logger = initialize_logger(__name__)

router = APIRouter(prefix="/admin/onboarding")


class OnboardingTokenBody(BaseModel):
    date_from: date
    date_to: date

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        if not self.date_from <= self.date_to:
            raise ValueError("Date From has to come before Date To")
        return self


@router.post("/tokens")
def generate_onboarding_token(body: OnboardingTokenBody) -> Response:
    """
    Onboarding Token generation endpoint.
    """
    try:
        token_svc = OnboardingTokenService()
        token = token_svc.build_onboarding_token(date_from=body.date_from, date_to=body.date_to)
        return JSONResponse(
            {
                "onboarding_token": token,
            }
        )
    except RuntimeError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
