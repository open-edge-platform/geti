// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Request, Route } from '@playwright/test';
import { Headers } from 'headers-polyfill';
import { context, DefaultBodyType, MockedResponse, ResponseComposition, ResponseTransformer } from 'msw';
import OpenAPIBackend from 'openapi-backend';

const CSRF_METHODS = ['POST', 'PUT', 'DELETE', 'PATCH'];
const CSRF_HEADER = 'x-geti-csrf-protection';

const getRequestBody = (request: Request, headers: { [key: string]: string }) => {
    if (headers['content-type']?.includes('multipart/form-data')) {
        return request.postData();
    }

    // Handle TUS uploads
    if (headers['content-type']?.includes('application/offset+octet-stream')) {
        return request.postDataBuffer();
    }

    try {
        return request.postDataJSON();
    } catch (_error: unknown) {
        console.warn('Could not determine request post data', request.method(), request.url(), request.headers());

        return undefined;
    }
};

export const handleRoute = async (route: Route, openApi: OpenAPIBackend, serverUrl: string) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());
    const headers = await request.allHeaders();

    // SDL requires us to add additional protection against CSRF, we do this by
    // passing a 'x-geti-csrf-protection' header with a default value of '1',
    // which is checked by the backend when making POST, PUT, DELETE or PATCH
    // requests.
    if (CSRF_METHODS.includes(method) && headers[CSRF_HEADER] !== '1') {
        console.error('Tried sending a non-simple request without a valid CSRF token');

        await route.abort('accessdenied');

        return false;
    }

    const path = url.href.slice(serverUrl.length);
    const body = getRequestBody(request, headers);

    const openApiRequest = {
        path,
        query: url.search,
        method,
        body,
        headers,
    };

    // This mimicks MSW v1.0's res function in that if the user calls,
    // res(ctx.status(201), ctx.json(body))
    // then it returns a response with said status and json by applying the provided transformers
    const res: Omit<ResponseComposition<DefaultBodyType>, 'once' | 'networkError'> = (
        ...contexts: ResponseTransformer<DefaultBodyType>[]
    ) => {
        const response: MockedResponse = {
            headers: new Headers(),
            status: 200,
            body: undefined,
            statusText: '',
            once: false,
            passthrough: false,
            delay: undefined,
        };

        contexts.forEach((responseTransformer) => {
            responseTransformer(response);
        });

        route.fulfill({
            status: response.status ?? 200,
            body: response.body,
            contentType: response.headers.get('Content-Type') ?? undefined,
            headers: Object.fromEntries(response.headers),
        });

        return response;
    };

    try {
        await openApi.handleRequest(openApiRequest, res, context);

        return true;
    } catch (error) {
        // OpenAPI was not configured to handle this route, or an issue occurred that made it fail
        console.error('Could not handle request', { openApiRequest, error, method, url });

        return false;
    }
};
