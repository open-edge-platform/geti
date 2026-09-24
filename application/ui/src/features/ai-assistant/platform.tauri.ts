// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

const isWindowsDesktop = (): boolean => typeof navigator !== 'undefined' && navigator.userAgent.includes('Windows NT');

export const isAssistantAvailable = (): boolean => true;
export const hasSecureAiBackend = isWindowsDesktop;
export const hasNativeAssistantApps = isWindowsDesktop;
