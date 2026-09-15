// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { DESKTOP_ONLY_MESSAGE } from './parse-response';

/**
 * Web build stub. On the desktop the `.tauri.ts` twin keeps the key in the
 * operating system credential store (Windows Credential Manager / Keychain),
 * where renderer JavaScript cannot read it back.
 */
export const hasStoredKey = (): Promise<boolean> => Promise.resolve(false);

export const saveKey = (_key: string): Promise<void> => Promise.reject(new Error(DESKTOP_ONLY_MESSAGE));

export const deleteKey = (): Promise<void> => Promise.resolve();
