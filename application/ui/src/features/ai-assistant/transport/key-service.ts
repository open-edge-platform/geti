// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { browserDeleteKey, browserHasStoredKey, browserReadStoredKey, browserSaveKey } from './browser-key-storage';

/**
 * Web build stub. On the desktop the `.tauri.ts` twin keeps the key in the
 * operating system credential store (Windows Credential Manager / Keychain),
 * where renderer JavaScript cannot read it back.
 */
export const hasStoredKey = browserHasStoredKey;

export const saveKey = browserSaveKey;

export const deleteKey = browserDeleteKey;

export const readStoredKey = browserReadStoredKey;
