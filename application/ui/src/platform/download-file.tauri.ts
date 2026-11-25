// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { toast } from '@/components/toast/toast.component';
import { i18n } from '@/i18n';
import { Channel, invoke } from '@tauri-apps/api/core';

export const downloadFile = (url: string, name?: string, startedMessage?: string): void => {
    void saveDownload(url, name, startedMessage);
};

// The shell shows the save dialog and streams the file to disk (`src-tauri/src/download.rs`).
const saveDownload = async (url: string, name?: string, startedMessage?: string): Promise<void> => {
    try {
        const fileName = name ?? getFallbackFilename(url);
        const onStarted = new Channel<null>();
        onStarted.onmessage = () => {
            if (startedMessage !== undefined) {
                toast({ type: 'info', message: startedMessage });
            }
        };
        const args = { fileName, filter: getFilterForFilename(fileName), onStarted };

        if (url.startsWith('data:')) {
            // The shell only downloads from the backend, so hand over the bytes instead (e.g. charts).
            const contents = Array.from(new Uint8Array(await (await fetch(url)).arrayBuffer()));
            await invoke('save_file', { ...args, contents });
        } else {
            await invoke('download_file', { ...args, url });
        }
    } catch (error: unknown) {
        console.error('[tauri downloadFile] failed', error);
        toast({ type: 'error', message: i18n.t('downloads.failure.genericError') });
    }
};

const getFilterForFilename = (filename: string): { name: string; extensions: string[] } => {
    const extension = filename.split('.').pop();

    if (extension === undefined || extension === '' || extension === filename) {
        return { name: i18n.t('downloads.saveDialog.allFiles'), extensions: ['*'] };
    }

    return {
        name: i18n.t('downloads.saveDialog.fileTypeFilter', { extension: extension.toUpperCase() }),
        extensions: [extension.toLowerCase()],
    };
};

const getFallbackFilename = (url: string): string => {
    if (url.startsWith('blob:')) {
        return 'download';
    }

    // Asset download URLs end with /binary, so the previous segment is usually the item id.
    const segments = new URL(url, window.location.origin).pathname.split('/').filter(Boolean);

    return segments.at(-2) ?? 'download';
};
