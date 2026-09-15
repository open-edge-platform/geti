// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/**
 * The assistant ships with the Windows desktop application only. The desktop
 * bundle is built from the same sources for every operating system, so the
 * check happens at runtime: WebView2 is the only webview whose user agent
 * reports `Windows NT`.
 */
export const isAssistantAvailable = (): boolean => navigator.userAgent.includes('Windows NT');
