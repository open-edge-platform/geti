// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { StreamRequest, StreamResult } from '../types';
import { DESKTOP_ONLY_MESSAGE } from './parse-response';

/**
 * Web build stub. The real implementation lives in the `.tauri.ts` twin, which
 * the bundler substitutes for desktop builds: the OpenAI request is made by the
 * Rust shell so the API key never enters renderer JavaScript.
 */
export const streamResponse = (_request: StreamRequest): Promise<StreamResult> => {
    return Promise.reject(new Error(DESKTOP_ONLY_MESSAGE));
};

export const cancelResponse = (_requestId: string): void => {
    // No request can be in flight on the web.
};
