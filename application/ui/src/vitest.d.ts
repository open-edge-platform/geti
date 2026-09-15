// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// Vitest 5 no longer reads matcher declarations from the global `jest.Matchers`
// interface, which is all `@testing-library/jest-dom` augments, so declare them here.

import type { TestingLibraryMatchers } from '@testing-library/jest-dom/matchers';

declare module 'vitest' {
    interface Matchers<
        R extends void | Promise<void> = void | Promise<void>,
        T = unknown,
    > extends TestingLibraryMatchers<unknown, R> {}
}
