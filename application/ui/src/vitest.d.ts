// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// Vitest 5 no longer reads matcher declarations from the global `jest.Matchers`
// interface, which is all `@testing-library/jest-dom` augments, so declare them here.

import type { TestingLibraryMatchers } from '@testing-library/jest-dom/matchers';

/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-empty-object-type */
declare module 'vitest' {
    // The type parameters must match Vitest's own `Matchers` declaration exactly for the merge to apply.
    interface Matchers<
        R extends void | Promise<void> = void | Promise<void>,
        T = unknown,
    > extends TestingLibraryMatchers<unknown, R> {}
}
/* eslint-enable @typescript-eslint/no-unused-vars, @typescript-eslint/no-empty-object-type */
