// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { invoke } from '@tauri-apps/api/core';

import { hasSecureAiBackend } from '../platform';
import { browserDeleteKey, browserHasStoredKey, browserReadStoredKey, browserSaveKey } from './browser-key-storage';

/**
 * The key itself is write-only from the webview's point of view: it is handed
 * to the shell once and only ever read back inside Rust.
 */
export const hasStoredKey = (account: string): Promise<boolean> =>
    hasSecureAiBackend() ? invoke<boolean>('assistant_key_status', { account }) : browserHasStoredKey(account);

export const saveKey = (account: string, key: string): Promise<void> =>
    hasSecureAiBackend() ? invoke('assistant_key_set', { account, key }) : browserSaveKey(account, key);

export const deleteKey = (account: string): Promise<void> =>
    hasSecureAiBackend() ? invoke('assistant_key_delete', { account }) : browserDeleteKey(account);

export const readStoredKey = (account: string): string | null =>
    hasSecureAiBackend() ? null : browserReadStoredKey(account);
