// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { invoke } from '@tauri-apps/api/core';

/**
 * The key itself is write-only from the webview's point of view: it is handed
 * to the shell once and only ever read back inside Rust.
 */
export const hasStoredKey = (): Promise<boolean> => invoke<boolean>('openai_key_status');

export const saveKey = (key: string): Promise<void> => invoke('openai_key_set', { key });

export const deleteKey = (): Promise<void> => invoke('openai_key_delete');
