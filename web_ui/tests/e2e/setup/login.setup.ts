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

import path from 'path';

import { setup } from './fixture';

setup('Login as user', async ({ page, loginPage, account }) => {
    await page.goto('/');
    await loginPage.login(account.email, account.password);

    // Store cookie and localstorage state so that we can reuse it in other tests
    const authFile = path.join(__dirname, '../.auth/user.json');
    await page.context().storageState({ path: authFile });
});
