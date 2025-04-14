// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
