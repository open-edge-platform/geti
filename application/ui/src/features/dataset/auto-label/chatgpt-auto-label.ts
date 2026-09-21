// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface ChatGptAutoLabelResult {
    selected: number;
    annotated: number;
    annotations: number;
}

export const runChatGptAutoLabel = async (
    _projectId: string,
    _onProgress: (message: string) => void
): Promise<ChatGptAutoLabelResult> => {
    throw new Error('ChatGPT Auto-Label is available in the Geti desktop app.');
};
