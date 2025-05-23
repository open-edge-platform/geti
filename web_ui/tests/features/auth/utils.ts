// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { Page } from '@playwright/test';
import { User } from 'oidc-client-ts';

import { generateToken as generateJWT } from '../../utils/generate-token';

export const routeLoginRequest = async (page: Page) => {
    await page.route('/dex/auth/regular_users*', async (route) => {
        const request = route.request();
        const url = new URL(request.url());

        // Normally the `authorization_endpoint` would return a login page which then returns a 303 response
        // when the login is successful.
        // Instead of showing a login page we act as if login was immediately successful
        const state = url.searchParams.get('state');
        const code = url.searchParams.get('code_challenge');
        await route.fulfill({
            status: 303,
            headers: {
                location: `${paths.authProviderCallback({})}?code=${code}&state=${state}`,
            },
        });
    });
};

export const recordTokensStoredBySetCookie = async (page: Page) => {
    const idTokens: string[] = [];
    await page.route('/api/v1/set_cookie', (route) => {
        const headers = route.request().headers();
        const token = headers['authorization'].split(' ').at(1);

        if (token) {
            idTokens.push(token);
        }

        route.fulfill({
            status: 200,
            headers: { 'Set-Cookie': `geti-cookie=${token}; HttpOnly; SameSite=Strict; Path=/` },
        });
    });

    return idTokens;
};

export const recordDexTokenRequests = async (page: Page, idToken: unknown) => {
    const requests: Array<{ grant_type: string; refresh_token: string }> = [];
    await page.route('/dex/token', (route) => {
        const data = route.request().postDataJSON();

        requests.push({
            grant_type: data.grant_type,
            refresh_token: data.refresh_token,
        });

        route.fulfill({
            status: 200,
            json: {
                access_token: '<redacted_new_access_token>',
                token_type: 'bearer',
                expires_in: 3600,
                refresh_token: '<redacted_new_refresh_token>',
                id_token: idToken,
            },
        });
    });

    return requests;
};

export const ADMIN_PROFILE: User['profile'] = {
    exp: 0,
    iat: 0,
    iss: '<redacted>',
    sub: '<redacted>',
    aud: 'web_ui',
    email: 'admin@intel.com',
    email_verified: true,
    name: 'Admin',
    preferred_username: 'Admin',
};

export const generateToken = async (payload: User['profile'] | undefined, expirationTime: number) => {
    return generateJWT(expirationTime, {
        ...payload,
        exp: expirationTime,
        iat: expirationTime,
    });
};

const generateOidcState = async (expirationTimeInSeconds: number) => {
    const idToken = await generateToken(ADMIN_PROFILE, expirationTimeInSeconds);

    return {
        id_token: idToken,
        session_state: null,
        access_token: '<redacted_access_token>',
        refresh_token: '<redacted_refresh_token>',
        token_type: 'bearer',
        scope: 'openid profile groups email offline_access',
        profile: ADMIN_PROFILE,
        expires_at: expirationTimeInSeconds,
    };
};

/**
 * Return an empty storage state so that the user is logged out
 */
export const emptyStorageState = async () => [];

/**
 * Set expiration time of the oidc session
 */
export const expiringOidcStorageState = (seconds: number) => {
    return async () => {
        const expirationTimeInSeconds = Date.now() / 1000 + seconds;
        const oidc = await generateOidcState(expirationTimeInSeconds);

        return [{ name: 'oidc.user:/dex:web_ui', value: JSON.stringify(oidc) }];
    };
};

export const profileResponse = {
    organizations: [
        {
            organizationName: 'Organization 1',
            userStatus: 'ACT',
            organizationStatus: 'ACT',
            organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
            organizationCreatedAt: '2024-10-04T10:04:24Z',
        },
    ],
    telemetryConsent: 'y',
    telemetryConsentAt: '2023-11-02T10:03:47.428474Z',
    userConsent: 'y',
    userConsentAt: '2023-11-02T10:03:47.428474Z',
};
