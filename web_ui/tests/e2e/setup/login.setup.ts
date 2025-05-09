// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import path from 'path';

import { getDirname } from '../../utils/get-dirname';
import { setup } from './fixture';

setup('Login as user', async ({ page, loginPage, account }) => {
    await page.goto('/');
    await loginPage.login(account.email, account.password);

    // Store cookie and localstorage state so that we can reuse it in other tests
    const authFile = path.join(getDirname(import.meta.url), '../.auth/user.json');
    await page.context().storageState({ path: authFile });
});
