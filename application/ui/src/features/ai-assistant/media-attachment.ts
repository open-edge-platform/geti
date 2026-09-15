// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ATTACHMENT_MAX_EDGE } from './config';
import type { ChatAttachment } from './types';

export interface MediaAttachmentSource {
    id: string;
    name: string;
    url: string;
}

const readAsDataUrl = (blob: Blob): Promise<string> =>
    new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onerror = () => reject(new Error('Could not read the image.'));
        reader.onload = () => resolve(String(reader.result));
        reader.readAsDataURL(blob);
    });

const loadImage = (dataUrl: string): Promise<HTMLImageElement> =>
    new Promise((resolve, reject) => {
        const image = new Image();

        image.onerror = () => reject(new Error('Could not decode the image.'));
        image.onload = () => resolve(image);
        image.src = dataUrl;
    });

/**
 * Media is downscaled before it is sent: the models bill per image tile, and a
 * 4K frame costs many times a 1280px one without adding usable detail.
 */
export const loadMediaAttachment = async (source: MediaAttachmentSource): Promise<ChatAttachment> => {
    const response = await fetch(source.url, { credentials: 'include' });

    if (!response.ok) {
        throw new Error(`Could not load "${source.name}".`);
    }

    const original = await readAsDataUrl(await response.blob());
    const image = await loadImage(original);

    const longestEdge = Math.max(image.naturalWidth, image.naturalHeight);

    if (longestEdge <= ATTACHMENT_MAX_EDGE) {
        return { id: source.id, name: source.name, dataUrl: original };
    }

    const scale = ATTACHMENT_MAX_EDGE / longestEdge;
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(image.naturalWidth * scale);
    canvas.height = Math.round(image.naturalHeight * scale);

    const context = canvas.getContext('2d');

    if (context === null) {
        return { id: source.id, name: source.name, dataUrl: original };
    }

    context.drawImage(image, 0, 0, canvas.width, canvas.height);

    return { id: source.id, name: source.name, dataUrl: canvas.toDataURL('image/jpeg', 0.85) };
};
