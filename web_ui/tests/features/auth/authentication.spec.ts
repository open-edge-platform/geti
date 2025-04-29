// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { test } from '../../fixtures/base-test';
import { testWithLocalStorageState } from '../../fixtures/open-api';
import {
    ADMIN_PROFILE,
    emptyStorageState,
    expiringOidcStorageState,
    generateToken,
    profileResponse,
    recordDexTokenRequests,
    recordTokensStoredBySetCookie,
    routeLoginRequest,
} from './utils';

/**
 * The UI uses OIDC (OpenID Connect) to authenticate with the Geti Rest API.
 * The tests below show how we use the PKCE grant to get a access and refresh
 * tokens as well as how we use the refresh token grant to refresh the tokens
 *
 * After authenticating with our OIDC provider another `set_cookie` endpoint is
 * used so that the server can set an HTTPOnly SameSite Strict cookie
 * This is done so that we don't need to manually provide the authorization header
 * to each request
 *
 * Note that the tests below are a bit different than other playwright tests: we
 * need to setup the user's localstorage state with testWithLocalStorageState
 * so that the test is either logged out, or logged in with a predefined access token
 */

test.describe('Authentication with the OpenID Connect protocol', () => {
    testWithLocalStorageState(test, emptyStorageState)(
        'It uses the proof key for code exchange protocol to log in',
        async ({ page, registerApiResponse }) => {
            // Only return a user profile if the UI sends a auth cookie
            registerApiResponse('User_get_user_profile', (req, res, ctx) => {
                if (req.cookies['geti-cookie'] === undefined) {
                    return res(ctx.status(403));
                }

                return res(ctx.status(200), ctx.json(profileResponse));
            });

            // After OIDC detects that we have an expired session we will ask dex for new tokens
            const newIdToken = await generateToken(ADMIN_PROFILE, Date.now() / 1000 + 3600);
            const tokenRequests = await recordDexTokenRequests(page, newIdToken);

            await routeLoginRequest(page);
            const idTokens = await recordTokensStoredBySetCookie(page);

            await page.goto('/');

            // Wait for the homepage to be visible, which happens after the `/profile`
            // endpoint returns data based on the precense of the `geti-cookie`
            await expect(page.getByLabel('intel geti')).toBeVisible();

            // Verify that we've set the authorization cookie
            expect(idTokens).toHaveLength(1);
            expect(idTokens).toEqual([newIdToken]);

            expect(tokenRequests).toHaveLength(1);
            expect(tokenRequests[0].grant_type).toEqual('authorization_code');
        }
    );

    testWithLocalStorageState(test, expiringOidcStorageState(-60))(
        "It logs in again when the user's auth token is expired",
        async ({ page, initialOidcUser: user }) => {
            // After OIDC detects that we have an expired session we will ask dex for new tokens
            const newIdToken = await generateToken(user?.profile, Date.now() / 1000 + 3600);
            const tokenRequests = await recordDexTokenRequests(page, newIdToken);

            await routeLoginRequest(page);
            const idTokens = await recordTokensStoredBySetCookie(page);

            await page.goto('/');

            await expect(page.getByLabel('intel geti')).toBeVisible();

            // Verify that we've set the authorization cookie twice: once on initial sign up
            // and another time when we refreshed the token
            expect(idTokens).toHaveLength(2);
            expect(idTokens).toEqual([user?.id_token, newIdToken]);

            expect(tokenRequests).toHaveLength(1);
            expect(tokenRequests[0].grant_type).toEqual('authorization_code');
        }
    );

    testWithLocalStorageState(test, expiringOidcStorageState(60))(
        "refreshing the user's id and access token",
        async ({ page, initialOidcUser: user }) => {
            // After OIDC detects that we have an expired session we will ask dex for new tokens
            const newIdToken = await generateToken(user?.profile, Date.now() / 1000 + 3600);
            const tokenRequests = await recordDexTokenRequests(page, newIdToken);

            const idTokens = await recordTokensStoredBySetCookie(page);

            await page.goto('/');

            await expect(page.getByLabel('intel geti')).toBeVisible();

            // Verify that we've set the authorization cookie twice: once on initial sign up
            // and another time when we refreshed the token
            await expect(() => {
                expect(idTokens).toHaveLength(2);
                expect(idTokens).toEqual([user?.id_token, newIdToken]);
            }).toPass();

            expect(tokenRequests[0]).toEqual({
                grant_type: 'refresh_token',
                refresh_token: '<redacted_refresh_token>',
            });
        }
    );

    test.describe('Error handling', () => {
        testWithLocalStorageState(test, expiringOidcStorageState(60))('Invalid refresh token', async ({ page }) => {
            page.route('/dex/token', (route) => {
                route.fulfill({
                    status: 400,
                    json: {
                        error: 'invalid_request',
                        error_description: 'Refresh token is invalid or has already been claimed by another client.',
                    },
                });
            });

            await page.goto('/');

            // First page load will be successful
            await expect(page.getByLabel('intel geti')).toBeVisible();

            // After trying to refresh the access token with an invalid refresh token we show a login error
            await expect(page.getByRole('heading', { name: 'Login error' })).toBeVisible();
        });

        test('User sees access denied when they do not have access to a profile', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('User_get_user_profile', (_, res, ctx) => {
                return res(ctx.status(401));
            });

            await page.goto('/');

            await expect(page.getByRole('heading', { name: 'Access denied' })).toBeVisible();
        });

        test('An error is shown when set_cookie returns an error', async ({ page }) => {
            await page.route('/api/v1/set_cookie', (route) => {
                route.fulfill({ status: 401 });
            });

            await page.goto('/');

            await expect(page.getByRole('heading', { name: 'Login error' })).toBeVisible();
        });
    });
});
