// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/**
 * Web build stub: the assistant needs the Rust shell to hold the API key and to
 * drive the ChatGPT app, so it is never offered outside the desktop build. The
 * `.tauri.ts` twin narrows it further, to Windows only.
 */
export const isAssistantAvailable = (): boolean => false;
