// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, test } from '../../fixtures/base-test';
import { notFoundHandler } from '../../fixtures/open-api/setup-open-api-handlers';
import { waitForLoadingToBeFinished } from '../../utils/assertions';
import { ACCOUNT_URL } from './mocks';

const ONE_MONTH_IN_MS = 1000 * 60 * 60 * 24 * 31;

const PERSONAL_ACCESS_TOKENS_PATH =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/users/77b5fa42-599e-4899-a4c0-daae13487289/personal_access_tokens';

test.describe('Profile page - personal access token', () => {
    test.beforeEach(async ({ page, openApi }) => {
        openApi.registerHandler('notFound', (c, res, ctx) => {
            if (c.request.method === 'get' && c.request.path === PERSONAL_ACCESS_TOKENS_PATH) {
                return res(ctx.status(204));
            }

            if (c.request.method === 'post' && c.request.path === PERSONAL_ACCESS_TOKENS_PATH) {
                const payload = c.request.body as {
                    expiresAt: string;
                    name: string;
                    description: string;
                };

                const token = {
                    id: 'a28bb7ae-612a-4f8c-9170-4d988c788d25',
                    partial: 'geti_pat_RokPEnvuaYs',
                    name: payload.name,
                    description: payload.description,
                    expiresAt: payload.expiresAt,
                    organizationId: 'a30b0133-05d9-4355-afe6-3a8ae8c36b1a',
                    userId: '4258d406-7063-4b03-92b2-3b7de081696f',
                    createdAt: new Date().toISOString(),
                    personalAccessToken: 'geti_test',
                };

                return res(ctx.status(200), ctx.json(token));
            }

            return notFoundHandler(c, res, ctx);
        });

        const personalAccessTokenUrl = ACCOUNT_URL('5b1f89f3-aba5-4a5f-84ab-de9abb8e0633', 'personal-access-token');
        await page.goto(personalAccessTokenUrl);

        await waitForLoadingToBeFinished(page);
    });

    test('Check tab elements', async ({ page }) => {
        await expect(page.getByText('Create Personal Access Token')).toBeInViewport();

        await expect(page.locator('#general-warning-message-id')).toHaveText(
            'When you use an Personal Access Token in your application, ' +
                'ensure that it is kept secure during both storage and transmission'
        );

        const createPATButton = page.getByRole('button', { name: 'Create' });
        await expect(createPATButton).toBeEnabled();
        await createPATButton.click();

        await expect(page.getByRole('dialog', { name: 'api-key-dialog' })).toBeVisible();
    });

    test('Check create personal access token dialog', async ({ personalAccessTokenPage }) => {
        const dialog = await personalAccessTokenPage.createToken();
        await dialog.setName('some api key name');
        await expect(dialog.name).toHaveValue('some api key name');

        await expect(dialog.cancelButton).toBeEnabled();
        await expect(dialog.createButton).toBeDisabled();

        //Note: Date.now were used to be able to select the date and check if proper value was put in the input
        //We have to know which date to select and it shouldn't be before today (not available in the component)
        //There are no operations on the date - it's save to use it
        //In the future we can think of mocking Date.now globally in the tests
        await dialog.fillExpirationDate(new Date(Date.now()));
        await expect(dialog.createButton).toBeEnabled();

        const token = await dialog.create();
        expect(token).not.toBeFalsy();
        expect(token).toEqual('geti_test');
    });

    test('Create a personal access token by setting the expiration date', async ({ personalAccessTokenPage }) => {
        const dialog = await personalAccessTokenPage.createToken();
        await dialog.setName('API Token from component test');
        await dialog.setDescription('A token used by component tests');

        const date = new Date(new Date().getTime() + ONE_MONTH_IN_MS);
        await dialog.setExpirationDate(date);

        const token = await dialog.create();
        expect(token).not.toBeFalsy();
        expect(token).toEqual('geti_test');
    });
});
