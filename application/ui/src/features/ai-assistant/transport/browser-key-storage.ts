// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

const keyName = (account: string): string => `geti.ai-assistant.credential.${account}`;

export const browserHasStoredKey = async (account: string): Promise<boolean> =>
    (window.localStorage.getItem(keyName(account)) ?? '').trim() !== '';

export const browserReadStoredKey = (account: string): string | null => window.localStorage.getItem(keyName(account));

export const browserSaveKey = async (account: string, key: string): Promise<void> => {
    window.localStorage.setItem(keyName(account), key);
};

export const browserDeleteKey = async (account: string): Promise<void> => {
    window.localStorage.removeItem(keyName(account));
};
