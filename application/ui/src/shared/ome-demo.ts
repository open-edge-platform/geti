// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MediaOmeImage, MediaOmePlane, OmeChannelSetting } from '@/api/types';

// TODO(#7810): demo-only. Fake OME images rendered in the browser until the backend serves real ones.

type ChannelKind = 'nuclei' | 'cytoplasm' | 'puncta';

type DemoChannel = { name: string; color: string; kind: ChannelKind };

export const OME_DEMO_INTENSITY_MAX = 4095;

const createDemoImage = (
    props: Pick<MediaOmeImage, 'id' | 'name' | 'width' | 'height' | 'size_z' | 'size_c' | 'size_t'>
): MediaOmeImage => ({
    type: 'ome_image',
    format: 'tiff',
    size: 0,
    ...props,
});

const DEMO_CHANNELS: Record<string, DemoChannel[]> = {
    '0e0e0e0e-0000-4000-8000-000000000001': [
        { name: 'DAPI', color: '#3B6CFF', kind: 'nuclei' },
        { name: 'GFP', color: '#27C46A', kind: 'cytoplasm' },
        { name: 'Cy5', color: '#E8503A', kind: 'puncta' },
    ],
    '0e0e0e0e-0000-4000-8000-000000000002': [
        { name: 'H2B-mCherry', color: '#FF00FF', kind: 'nuclei' },
        { name: 'Tubulin-GFP', color: '#00FF00', kind: 'cytoplasm' },
    ],
};

export const OME_DEMO_IMAGES: MediaOmeImage[] = [
    createDemoImage({
        id: '0e0e0e0e-0000-4000-8000-000000000001',
        name: 'hela-z-stack.ome.tiff',
        width: 1024,
        height: 768,
        size_z: 24,
        size_c: 3,
        size_t: 1,
    }),
    createDemoImage({
        id: '0e0e0e0e-0000-4000-8000-000000000002',
        name: 'mitosis-time-lapse.ome.tiff',
        width: 768,
        height: 768,
        size_z: 6,
        size_c: 2,
        size_t: 16,
    }),
];

export const getOmeDemoChannelNames = (mediaId: string): string[] =>
    (DEMO_CHANNELS[mediaId] ?? []).map(({ name }) => name);

export const getOmeDemoDefaultChannels = (mediaId: string): OmeChannelSetting[] =>
    (DEMO_CHANNELS[mediaId] ?? []).map(({ color }, channel) => ({
        channel,
        enabled: true,
        color,
        window_min: Math.round(OME_DEMO_INTENSITY_MAX * 0.05),
        window_max: Math.round(OME_DEMO_INTENSITY_MAX * 0.75),
    }));

// Cells are ellipsoids, so each Z slice cuts them at a different radius, and they drift between time points.
type Cell = {
    x: number;
    y: number;
    z: number;
    radius: number;
    depth: number;
    brightness: number;
    vx: number;
    vy: number;
};

const createRandom = (seedText: string) => {
    let seed = [...seedText].reduce((hash, char) => Math.imul(hash ^ char.charCodeAt(0), 16777619), 2166136261) >>> 0;

    // mulberry32
    return () => {
        seed = (seed + 0x6d2b79f5) >>> 0;
        let value = seed;
        value = Math.imul(value ^ (value >>> 15), value | 1);
        value ^= value + Math.imul(value ^ (value >>> 7), value | 61);

        return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
    };
};

const between = (random: () => number, min: number, max: number) => min + random() * (max - min);

const createCells = (seedText: string, count: number, sizeZ: number, radius: [number, number]): Cell[] => {
    const random = createRandom(seedText);

    return Array.from({ length: count }, () => ({
        x: random(),
        y: random(),
        z: between(random, 0, sizeZ - 1),
        radius: between(random, ...radius),
        depth: between(random, Math.max(1.5, sizeZ / 6), Math.max(2, sizeZ / 3)),
        brightness: between(random, 0.55, 0.95),
        vx: between(random, -0.006, 0.006),
        vy: between(random, -0.006, 0.006),
    }));
};

const getChannelCells = (mediaId: string, sizeZ: number, kind: ChannelKind): Cell[] => {
    const cells = createCells(mediaId, 36, sizeZ, [0.03, 0.055]);

    if (kind === 'nuclei') {
        return cells;
    }

    if (kind === 'cytoplasm') {
        return cells.map((cell) => ({ ...cell, radius: cell.radius * 2.1, depth: cell.depth * 1.4, brightness: 0.4 }));
    }

    return createCells(`${mediaId}-puncta`, 260, sizeZ, [0.005, 0.01]);
};

const renderChannelIntensity = (cells: Cell[], seed: number, z: number, t: number, width: number, height: number) => {
    const intensity = new Float32Array(width * height);
    const background = OME_DEMO_INTENSITY_MAX * 0.04;

    for (let index = 0; index < intensity.length; index++) {
        const noise = (Math.imul(index ^ seed, 2654435761) >>> 0) / 4294967296;
        intensity[index] = background * (0.6 + noise);
    }

    const scale = Math.min(width, height);

    cells.forEach((cell) => {
        const zDistance = (z - cell.z) / cell.depth;

        if (Math.abs(zDistance) >= 1) {
            return;
        }

        const radius = cell.radius * scale * Math.sqrt(1 - zDistance ** 2);
        const centerX = ((((cell.x + cell.vx * t) % 1) + 1) % 1) * width;
        const centerY = ((((cell.y + cell.vy * t) % 1) + 1) % 1) * height;
        const peak = cell.brightness * OME_DEMO_INTENSITY_MAX;

        for (let y = Math.max(0, Math.floor(centerY - radius)); y < Math.min(height, centerY + radius); y++) {
            for (let x = Math.max(0, Math.floor(centerX - radius)); x < Math.min(width, centerX + radius); x++) {
                const distance = ((x - centerX) ** 2 + (y - centerY) ** 2) / radius ** 2;

                if (distance < 1) {
                    intensity[y * width + x] += peak * (1 - distance) ** 1.5;
                }
            }
        }
    });

    return intensity;
};

// Window/level each enabled channel, then add them up, like the backend renderer will.
const renderPlane = (
    mediaId: string,
    sizeZ: number,
    channels: OmeChannelSetting[],
    { z, t, width, height }: { z: number; t: number; width: number; height: number }
): ImageData => {
    const rgb = new Float32Array(width * height * 3);
    const kinds = DEMO_CHANNELS[mediaId] ?? [];

    channels
        .filter(({ enabled }) => enabled)
        .forEach(({ channel, color, window_min, window_max }) => {
            const kind = kinds[channel]?.kind;

            if (kind === undefined) {
                return;
            }

            const intensity = renderChannelIntensity(
                getChannelCells(mediaId, sizeZ, kind),
                channel + 1,
                z,
                t,
                width,
                height
            );
            const value = parseInt(color.replace('#', ''), 16);
            const [red, green, blue] = [(value >> 16) & 255, (value >> 8) & 255, value & 255];

            for (let index = 0; index < intensity.length; index++) {
                const level = Math.min(1, Math.max(0, (intensity[index] - window_min) / (window_max - window_min)));

                rgb[index * 3] += level * red;
                rgb[index * 3 + 1] += level * green;
                rgb[index * 3 + 2] += level * blue;
            }
        });

    const imageData = new ImageData(width, height);

    for (let index = 0; index < width * height; index++) {
        imageData.data[index * 4] = rgb[index * 3];
        imageData.data[index * 4 + 1] = rgb[index * 3 + 1];
        imageData.data[index * 4 + 2] = rgb[index * 3 + 2];
        imageData.data[index * 4 + 3] = 255;
    }

    return imageData;
};

export const renderOmeDemoPlane = (plane: MediaOmePlane): ImageData =>
    renderPlane(plane.id, plane.size_z, plane.channels, {
        z: plane.z_index,
        t: plane.t_index,
        width: plane.width,
        height: plane.height,
    });

const thumbnails = new Map<string, string>();

export const getOmeDemoThumbnailUrl = (image: MediaOmeImage): string => {
    const cached = thumbnails.get(image.id);

    if (cached !== undefined) {
        return cached;
    }

    const width = 320;
    const height = Math.round((width * image.height) / image.width);
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    canvas.getContext('2d')?.putImageData(
        renderPlane(image.id, image.size_z, getOmeDemoDefaultChannels(image.id), {
            z: Math.floor(image.size_z / 2),
            t: 0,
            width,
            height,
        }),
        0,
        0
    );

    const url = canvas.toDataURL('image/png');
    thumbnails.set(image.id, url);

    return url;
};
