// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MockedResponse } from 'msw';
import { ParsedRequest } from 'openapi-backend';
import type { OpReturnType } from 'openapi-typescript-fetch';

import { operations } from './generated/schemas';

// This file contains type helpers that allow us to use inference from OpenAPI to determine the
// request and response types from the server.
// @example:
// type CreateDatasetResponse = OpenApiResponse<"CreateDataset">
// type CreateDatasetRequest = OpenApiRequest<"CreateDataset">

// These helpers are very similar to the ones found in 'openapi-typescript-fetch'
// but they are not used / exported from this package
export type OpQueryType<OP> = OP extends { parameters?: { query?: infer Query } } ? Query : Record<string, never>;
export type OpPathType<OP> = OP extends { parameters?: { path?: infer Path } } ? Path : string;
export type OpBodyType<OP> = OP extends { requestBody?: { content: { 'application/json': infer Body } } }
    ? Body
    : Record<string, never>;

export type OperationId = keyof operations;

export type OpenApiRequestBody<OpId extends OperationId> = OpBodyType<operations[OpId]>;
export interface OpenApiRequest<OpId extends OperationId> extends Omit<ParsedRequest, 'body' | 'path' | 'query'> {
    path: OpPathType<operations[OpId]>;
    query: OpQueryType<operations[OpId]>;
    body: OpBodyType<operations[OpId]>;
}

export type OpenApiResponseBody<OpId extends OperationId> = OpReturnType<operations[OpId]>;

type UnknownToObject<T> = T extends unknown ? Record<string, unknown> : T;
//@ts-expect-error ignore
export type OpenApiResponse<OpId extends OperationId> = MockedResponse<UnknownToObject<OpReturnType<operations[OpId]>>>;
