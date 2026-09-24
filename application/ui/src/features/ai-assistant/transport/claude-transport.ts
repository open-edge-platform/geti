// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AssistantAccount, CodexLocation, StreamRequest, StreamResult } from '../types';
import { DESKTOP_ONLY_MESSAGE } from './parse-response';

export const claudeStatus = (): Promise<AssistantAccount | null> => Promise.resolve(null);
export const claudeLocate = (): Promise<CodexLocation> => Promise.resolve({ path: null, searched: [] });
export const claudeLogin = (): Promise<void> => Promise.reject(new Error(DESKTOP_ONLY_MESSAGE));
export const claudeLogout = (): Promise<void> => Promise.resolve();
export const pickClaudeBinary = (): Promise<string | null> => Promise.resolve(null);

export const claudeRespond = (_request: StreamRequest): Promise<StreamResult> =>
    Promise.reject(new Error(DESKTOP_ONLY_MESSAGE));

export const claudeCancel = (_requestId: string): void => undefined;
