// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/**
 * Replaces provider API key fragments in user-facing error text. The word
 * boundary keeps ordinary words such as "task-42" untouched.
 */
export const redactSecrets = (text: string): string => text.replace(/\bsk-(?:ant-)?[A-Za-z0-9_-]+/g, '***');
