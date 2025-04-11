// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import * as fs from 'fs';
import * as https from 'https';

import { ProxyConfig } from '@rsbuild/core';
import { responseInterceptor } from 'http-proxy-middleware';
import { HttpsProxyAgent } from 'https-proxy-agent';

const API_PROXY_PATH = process.env.REACT_APP_API_PROXY ?? '';

const GETI_DEV_DOMAIN = process.env.REACT_APP_GETI_DEV_DOMAIN ?? '';
const GETI_STAGING_DOMAIN = process.env.REACT_APP_GETI_STAGING_DOMAIN ?? '';
const GETI_CONFIG_DOMAIN = process.env.REACT_APP_GETI_CONFIG_DOMAIN ?? '';
const MEDIA_HOST_DOMAIN = process.env.REACT_APP_MEDIA_HOST_DOMAIN ?? '';

const API = API_PROXY_PATH.replace(/\/$/, '');

/*
    This proxy is used for development purposes. It allows us to develop and serve
    the UI locally on localhost while using a (possibly remote) server.
    The environment variable REACT_APP_API_PROXY determines this server.
*/

// when we request localhost:3000/intel-admin/deployment-config.json etc we will forward the request
// to the configured server (via API) and return its response
const proxyPaths = [
    '/intel-admin/deployment-config.json',
    '/deployment-config.json',
    '/api/',
    '/docs',
    '/dex',
    '/smtp4dev/',
];

// These settings are used to retrieve the OIDC configuration when using CIDaaS
const CSP_CONNECT = process.env.REACT_APP_GETI_CSP_CONNECT_DOMAIN ?? '';
const proxy = process.env.HTTPS_PROXY ?? process.env.HTTP_PROXY ?? '';
const useProxy =
    proxy && (API.includes(GETI_DEV_DOMAIN) || API.includes(GETI_STAGING_DOMAIN) || API.includes('intel.com'));

const agent = useProxy
    ? new HttpsProxyAgent<string>(proxy, { rejectUnauthorized: false })
    : new https.Agent({ rejectUnauthorized: false });

export const devProxy: ProxyConfig = [
    {
        context: ['/api/v1/feature_flags'],
        target: API_PROXY_PATH,
        agent,

        changeOrigin: true,
        secure: false,

        // Overwrite the server's side feature flags with our own
        selfHandleResponse: true,
        onProxyRes: responseInterceptor(async (buffer, res, _req) => {
            // The server will return an error message with text/plain format
            // when the UI uses an invalid JWT key.
            // In this case we return the original response to trigger a login error
            if (res.headers['content-type'] === 'text/plain') {
                return buffer;
            }

            const originalFeatureFlags = JSON.parse(buffer.toString('utf8'));
            try {
                const featureFlags = JSON.parse(String(fs.readFileSync('./dev-feature-flags.json')));

                return JSON.stringify({ ...originalFeatureFlags, ...featureFlags });
            } catch {
                return JSON.stringify(originalFeatureFlags);
            }
        }),
    },
    {
        context: proxyPaths,
        target: API_PROXY_PATH,
        agent,
        changeOrigin: true,
        secure: false,
        headers: {
            'Cross-Origin-embedder-Policy': 'require-corp',
            'Cross-Origin-opener-Policy': 'same-origin',
            'Content-Security-Policy':
                "frame-ancestors 'none'; " +
                "default-src 'self'; " +
                `connect-src 'self' ${API} ${CSP_CONNECT} ${GETI_CONFIG_DOMAIN} data:;` +
                `style-src 'self' 'unsafe-inline'; ` +
                `script-src 'self' ${API} 'unsafe-eval' blob:; ` +
                `media-src 'self' ${API} ${MEDIA_HOST_DOMAIN} ` +
                `https://docs.geti.intel.com blob: data:; ` +
                `img-src 'self' ${API} data:; ` +
                `frame-src 'none'; ` +
                `object-src 'none'; ` +
                `form-action 'self'; ` +
                `worker-src 'self' blob:`,
        },
        onProxyRes: (proxyResponse, request) => {
            if (
                request.url?.includes('set_cookie') &&
                request.method === 'POST' &&
                proxyResponse.headers['set-cookie']
            ) {
                const cookies = proxyResponse.headers['set-cookie'].map((cookie) => {
                    // We don't have https in local development so we need to remove the Secure option
                    return cookie.replace('Secure; ', '');
                });

                proxyResponse.headers['set-cookie'] = cookies;
            }
            // When using the import dataset feature (i.e. using TUS) we want to change the
            // location header so that it always points to localhost, which then uses this proxy
            // Example:
            // Input: https://10.211.120.131/api/v1/workspaces/x/datasets/uploads/resumable/62da8fcf70d82a88a983e75b
            // Output: http://localhost:3000/api/v1/workspaces/x/datasets/uploads/resumable/62da8fcf70d82a88a983e75b
            if ('location' in proxyResponse.headers) {
                // There are some other requests that can send a redirect / location header, which
                // we don't want to change. Specifically changing the redirect from the auth endpoint
                // can result in redirect loops
                const contentType = proxyResponse.headers['content-type'] ?? '';

                if (
                    !proxyResponse.headers.location?.includes('uploads/resumable') &&
                    !contentType.includes('video') &&
                    !contentType.includes('zip')
                ) {
                    return;
                }

                // Make sure there is only 1 forward slash
                const serverAddress = `${API}/`.replace(/\/\/+$/, '/');
                const requestOrigin = request.headers.origin ?? `http://${request.headers.host}`;
                const origin = (requestOrigin + '/').replace(/\/+$/g, '/');

                // Replace the server's address with localhost so that (dataset) import requests using tus will
                // first go through our proxy server, which solves CORS and SSL issues for local development
                const location = proxyResponse.headers.location?.replace(serverAddress, origin);

                proxyResponse.headers.location = location;
            }
        },
    },
];
