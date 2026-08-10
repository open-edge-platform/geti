// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Page } from '@playwright/test';

interface TauriInternals {
    metadata: {
        currentWindow: { label: string };
        currentWebview: { windowLabel: string; label: string };
    };
}

declare global {
    interface Window {
        // `@tauri-apps/api` reads this at runtime but ships no global type for it.
        __TAURI_INTERNALS__?: TauriInternals;
    }
}

/**
 * The Tauri desktop bundle (files resolved via the `.tauri.*` extension) calls
 * `@tauri-apps/api` at module load, e.g. `getCurrentWindow()` in
 * `src/platform/storage-cleanup.tauri.ts`. Those functions dereference
 * `window.__TAURI_INTERNALS__`, which is injected by the real Tauri webview
 * runtime and is therefore absent in Playwright's plain Chromium. Without it the
 * app throws `Cannot read properties of undefined (reading 'metadata')` before
 * React renders.
 */
export const mockTauriRuntime = async (page: Page): Promise<void> => {
    await page.addInitScript(() => {
        const label = 'main';

        // eslint-disable-next-line no-underscore-dangle -- required global name injected by the Tauri runtime
        window.__TAURI_INTERNALS__ = {
            metadata: {
                currentWindow: { label },
                currentWebview: { windowLabel: label, label },
            },
        };

        // eslint-disable-next-line no-underscore-dangle -- required global name injected by the Tauri runtime
        window.__TAURI_EVENT_PLUGIN_INTERNALS__ = {
            unregisterListener: () => {},
        };
    });
};
