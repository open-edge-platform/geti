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

import { setupServer } from 'msw/node';

// This configures a request mocking server with the given request handlers.

export const server = setupServer();

// Establish API mocking before all tests.

beforeAll(() => server.listen());

// Reset any request handlers that we may add during the tests,

// so they don't affect other tests.

afterEach(() => server.resetHandlers());

// Clean up after the tests are finished.

afterAll(() => server.close());
