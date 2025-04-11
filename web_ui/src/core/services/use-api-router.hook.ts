// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo } from 'react';

import isFunction from 'lodash/isFunction';
import isString from 'lodash/isString';

import { API_URLS } from './urls';
import { useDeploymentConfigQuery } from './use-deployment-config-query.hook';

// A route can be defined either as a constant string or a function returning a stirng
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type URL_Function = ((...args: any[]) => string) | string;

// The API_URLS object is recursive, so we need to wrap it recursively
type URL_Object = URL_Function | { [index: string]: URL_Object };

// Prefix the given route with a baseUrl where make sure the returned url is
// of the form "https//${baseUrl}/api/v1/the-route"
const prefixBaseUrl = (baseUrl: string, route: string | undefined) => {
    if (route === undefined) {
        return baseUrl;
    }

    if (route.startsWith('http')) {
        return route;
    }

    if (route.startsWith('v1')) {
        return `${baseUrl}/api/${route}`;
    }

    if (route.startsWith('/api')) {
        return `${baseUrl}${route}`;
    }

    if (route.startsWith('api')) {
        return `${baseUrl}/${route}`;
    }

    return `${baseUrl}/api/${route}`;
};

// Recursively wrap the urlObject so that when called the returned url witll be
// prefixed with the baseUrl
const prefixWithBaseUrl = (baseUrl: string, urlObject: URL_Object): URL_Object => {
    // API_URLS contains functions returning strings
    if (isFunction(urlObject)) {
        return (...args: unknown[]) => {
            return prefixBaseUrl(baseUrl, urlObject(...args));
        };
    }

    // API_URLS contains some constants
    if (isString(urlObject)) {
        return prefixBaseUrl(baseUrl, urlObject);
    }

    // API_URLS is an object containing other URL_Objects
    const newUrlObject: typeof urlObject = {};
    Object.keys(urlObject).forEach((urlKey) => {
        newUrlObject[urlKey] = prefixWithBaseUrl(baseUrl, urlObject[urlKey]);
    });

    return newUrlObject;
};

export const addHostToApiUrls = (url: string) => {
    return prefixWithBaseUrl(url, API_URLS) as API_URLS_TYPE;
};

// This hook returns a router that acts exactly the same as API_URLS in that you
// can call, API_URLS.WORKSPACES(workspaceIdentifier) and get back the url for getting
// projects.
// However instead of returning /api/v1/organizations/x/workspaces it returns a full url,
// https://${baseUrl}/api/v1/organizations/x/workspaces
// This allows us use different baseUrls depending on the deployment configuration
type API_URLS_TYPE = typeof API_URLS;
export const useApiRouter = (): API_URLS_TYPE => {
    const deploymentConfig = useDeploymentConfigQuery();

    return useMemo(() => {
        return addHostToApiUrls(deploymentConfig?.data?.controlPlaneUrl ?? '');
    }, [deploymentConfig]);
};
