// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { CodexAccount, CodexLocation, CodexModel, StreamRequest, StreamResult } from '../types';
import { DESKTOP_ONLY_MESSAGE } from './parse-response';

/**
 * Web build stub. The `.tauri.ts` twin drives the locally installed
 * ChatGPT/Codex app through the Rust shell.
 */
export const codexStatus = (_forceRefresh = false): Promise<CodexAccount | null> => Promise.resolve(null);

export const codexModels = (): Promise<CodexModel[]> => Promise.resolve([]);

export const codexLocate = (): Promise<CodexLocation> => Promise.resolve({ path: null, searched: [] });

export const codexDiagnostics = (): Promise<string> => Promise.resolve(DESKTOP_ONLY_MESSAGE);

export const pickCodexBinary = (): Promise<string | null> => Promise.resolve(null);

export const codexLogin = (_onUrl: (url: string) => void): Promise<void> =>
    Promise.reject(new Error(DESKTOP_ONLY_MESSAGE));

export const codexLogout = (): Promise<void> => Promise.resolve();

export const codexRespond = (_request: StreamRequest): Promise<StreamResult> =>
    Promise.reject(new Error(DESKTOP_ONLY_MESSAGE));

export const codexCancel = (_requestId: string): void => {
    // No operation can be in flight on the web.
};
