// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import https from 'https';

import { addHostToApiUrls, API_URLS } from '@geti/core';
import { ApplicationServices } from '@geti/core/src/services/application-services.interface';
import Headers from '@mjackson/headers';
import { APIRequestContext, test as baseTest } from '@playwright/test';
import axios, { AxiosAdapter, AxiosHeaders } from 'axios';

import { getApiServices } from '../../packages/core/src/services/get-api-services';

export interface ServiceConfiguration {
    router: typeof API_URLS;
    instance: ReturnType<typeof axios.create>;
}

const getPlaywrightRequestAdapter = (requestContext: APIRequestContext): AxiosAdapter => {
    return async (config) => {
        if (config.url === undefined) {
            throw new Error('Did not receive a URL');
        }

        type Payload = Parameters<typeof requestContext.fetch>[1];
        const payload: Payload = {
            headers: config.headers,
            method: config.method,
            failOnStatusCode: true,
        };

        const isMultipartUpload = config.data instanceof FormData;
        if (isMultipartUpload) {
            // Fixes a bug related "Multipart boundary not found" due to Axios
            // setting a the Content-Type header to `multipart/form-data` which
            // does not include the boundary that is used by Playwright
            if (payload.headers) {
                delete payload.headers['Content-Type'];
            }
            payload.multipart = config.data;
        } else {
            payload.data = config.data;
        }

        // Remove cookie set by Playwright's storage state when we explicitely
        // use a Geti api key
        if (payload.headers && 'x-api-key' in payload.headers) {
            // Set cookie to be empty so that Playwright won't overwrite it when
            // it is undefined
            payload.headers['cookie'] = '';
        }

        const response = await requestContext.fetch(config.url, payload);

        const headers = new Headers(response.headers());
        const isJson = headers.contentType.mediaType === 'application/json';
        const data = isJson ? await response.json() : await response.body();

        const status = response.status();
        const statusText = response.statusText();

        const axiosResponse = {
            ...response,
            data,
            config,
            status,
            statusText,
            headers: new AxiosHeaders(headers.toString()),
        };

        return axiosResponse;
    };
};

const getApiServiceConfiguration = (
    baseURL: string,
    apiKey: string,
    requestContext: APIRequestContext
): ServiceConfiguration => {
    const instance = axios.create({
        // Use a predefined api key
        headers: { 'x-api-key': apiKey },

        // Disable proxy and ignore ssl certificate errors when using internal BMs
        proxy: false,
        httpsAgent: new https.Agent({ rejectUnauthorized: false }),

        // Provide a playwright adapter so that all API requests from the tests
        // will be logged and reported in Playwright trace viewer
        adapter: getPlaywrightRequestAdapter(requestContext),
    });

    const router = addHostToApiUrls(baseURL);

    return { instance, router };
};

export const test = baseTest.extend<{
    apiServiceConfiguration: ReturnType<typeof getApiServiceConfiguration>;
    applicationServices: ApplicationServices;
}>({
    /**
     * The apiServiceConfiguration fixture can be used when we want to interact
     * with the REST API via our api services
     *
     * @example
     * const workspaceService = createApiWorkspacesService(apiServiceConfiguration);
     * const workspaces = await workspaceService.getWorkspaces(organizationId);
     */
    apiServiceConfiguration: async ({ baseURL, request }, use) => {
        const apiToken = process.env.PW_E2E_PERSONAL_ACCESS_TOKEN;

        if (baseURL === undefined) {
            throw new Error('Please define a baseURL on which we run our tests');
        }

        if (apiToken === undefined) {
            throw new Error('Please configure a PAT token to be used as our API token');
        }

        await use(getApiServiceConfiguration(baseURL, apiToken, request));
    },
    /**
     * The applicationServices fixture can be used to get an api service that has
     * been configured to use an api token to connect with a Geti platform
     *
     * @example
     * const workspaceService = apiServiceConfiguration.workspacesService
     * const workspaces = await workspaceService.getWorkspaces(organizationId);
     */
    applicationServices: async ({ apiServiceConfiguration }, use) => {
        await use(getApiServices(apiServiceConfiguration));
    },
});
