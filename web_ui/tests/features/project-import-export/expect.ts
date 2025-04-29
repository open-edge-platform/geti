// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

//Playwright does not have an API for request assertion and in this case we need to asser that the API was called
//with some attributes, this codes 'asserts' it by returning true or fail after 3000ms
export const expectRequestProjectImport = (page: Page, fileId: string) =>
    page.waitForResponse(async (response) => response.url().includes(`/jobs/${fileId}`), {
        timeout: 3000,
    });
