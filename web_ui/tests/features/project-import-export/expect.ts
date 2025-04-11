// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Page } from '@playwright/test';

//Playwright does not have an API for request assertion and in this case we need to asser that the API was called
//with some attributes, this codes 'asserts' it by returning true or fail after 3000ms
export const expectRequestProjectImport = (page: Page, fileId: string) =>
    page.waitForResponse(async (response) => response.url().includes(`/jobs/${fileId}`), {
        timeout: 3000,
    });
