// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotationDTO, DatasetSubset, MediaOmeImage, OmeChannelSetting } from '@/api/types';
import { bypass, http, HttpResponse } from 'msw';
import { setupWorker } from 'msw/browser';

import { getOmeDemoChannelView, OME_DEMO_IMAGES, renderOmeDemoPlane } from './ome-demo';

// TODO(#7810): delete once the OME backend is merged. Answers the OME endpoints of application/docs/ome.md for the
// fake images, so the app code is the same as with the real backend. Requests for any other media go to the network.

const MEDIA_PATH = '*/api/projects/:projectId/dataset/media';
const THUMBNAIL_WIDTH = 320;
const CHANNEL_PATTERN = /^(\d+)\|(\d+):(\d+)\$([0-9A-F]{6})$/i;

type SavedAnnotations = { annotations: AnnotationDTO[]; subset: DatasetSubset };

const annotationsByPlane = new Map<string, SavedAnnotations>();

const findImage = (mediaId: string | readonly string[] | undefined) => OME_DEMO_IMAGES.find(({ id }) => id === mediaId);

const getPlaneKey = (mediaId: string, url: URL) =>
    `${mediaId}-z${url.searchParams.get('z') ?? 0}-t${url.searchParams.get('t') ?? 0}`;

const withAnnotationStatus = (image: MediaOmeImage): MediaOmeImage => ({
    ...image,
    annotation_status: {
        has_annotations: [...annotationsByPlane.keys()].some((key) => key.startsWith(`${image.id}-`)),
    },
});

// `c` is `<index>|<min>:<max>$<RRGGBB>` per shown channel, comma-separated
const parseChannels = (c: string): OmeChannelSetting[] | undefined => {
    const matches = c
        .split(',')
        .filter((entry) => entry !== '')
        .map((entry) => CHANNEL_PATTERN.exec(entry));

    if (matches.some((match) => match === null)) {
        return undefined;
    }

    return matches.map((match) => {
        const [, channel, min, max, color] = match as RegExpExecArray;

        return {
            channel: Number(channel),
            enabled: true,
            color: `#${color}`,
            window_min: Number(min),
            window_max: Number(max),
        };
    });
};

const pngResponse = async (imageData: ImageData) => {
    const canvas = new OffscreenCanvas(imageData.width, imageData.height);
    canvas.getContext('2d')?.putImageData(imageData, 0, 0);

    return new HttpResponse(await canvas.convertToBlob({ type: 'image/png' }), {
        headers: { 'Content-Type': 'image/png' },
    });
};

const handlers = [
    // The fake images lead the first page of the gallery
    http.get(MEDIA_PATH, async ({ request }) => {
        const response = await fetch(bypass(request));

        if (!response.ok || Number(new URL(request.url).searchParams.get('offset') ?? 0) > 0) {
            return response;
        }

        const page = await response.json();

        return HttpResponse.json({ ...page, items: [...OME_DEMO_IMAGES.map(withAnnotationStatus), ...page.items] });
    }),

    http.get(`${MEDIA_PATH}/:mediaId`, ({ params }) => {
        const image = findImage(params.mediaId);

        return image && HttpResponse.json(withAnnotationStatus(image));
    }),

    http.get(`${MEDIA_PATH}/:mediaId/thumbnail`, ({ params }) => {
        const image = findImage(params.mediaId);

        if (image === undefined) {
            return;
        }

        return pngResponse(
            renderOmeDemoPlane(image, {
                z: Math.floor(image.size_z / 2),
                t: Math.floor(image.size_t / 2),
                channels: getOmeDemoChannelView(image.id),
                width: THUMBNAIL_WIDTH,
                height: Math.round((THUMBNAIL_WIDTH * image.height) / image.width),
            })
        );
    }),

    http.get(`${MEDIA_PATH}/:mediaId/render`, ({ params, request }) => {
        const image = findImage(params.mediaId);

        if (image === undefined) {
            return;
        }

        const { searchParams } = new URL(request.url);
        const c = searchParams.get('c');
        const channels = c === null ? getOmeDemoChannelView(image.id) : parseChannels(c);

        if (channels === undefined) {
            return HttpResponse.json({ detail: `Malformed channel view: ${c}` }, { status: 400 });
        }

        return pngResponse(
            renderOmeDemoPlane(image, {
                z: Number(searchParams.get('z') ?? 0),
                t: Number(searchParams.get('t') ?? 0),
                channels,
                width: image.width,
                height: image.height,
            })
        );
    }),

    http.get(`${MEDIA_PATH}/:mediaId/annotations`, ({ params, request }) => {
        const image = findImage(params.mediaId);

        if (image === undefined) {
            return;
        }

        const saved = annotationsByPlane.get(getPlaneKey(image.id, new URL(request.url)));

        return saved === undefined
            ? HttpResponse.json({ detail: 'Media has not been annotated yet' }, { status: 404 })
            : HttpResponse.json({ ...saved, user_reviewed: true });
    }),

    http.post(`${MEDIA_PATH}/:mediaId/annotations`, async ({ params, request }) => {
        const image = findImage(params.mediaId);

        if (image === undefined) {
            return;
        }

        const saved = (await request.json()) as SavedAnnotations;
        annotationsByPlane.set(getPlaneKey(image.id, new URL(request.url)), saved);

        return HttpResponse.json({ ...saved, user_reviewed: true }, { status: 201 });
    }),
];

export const startOmeDemoWorker = () => setupWorker(...handlers).start({ onUnhandledRequest: 'bypass', quiet: true });
