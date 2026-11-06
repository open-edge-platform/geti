// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { canRasteriseAtFullSize, getImageData, loadImageData, projectPointOnLine } from './utils';

const createImage = (width: number, height: number): ImageBitmap => ({ width, height, close: rs.fn() }) as ImageBitmap;

const createCanvasContext = () => {
    return {
        drawImage: rs.fn(),
        getImageData: rs.fn((_x: number, _y: number, width: number, height: number) => {
            return {
                width,
                height,
                data: new Uint8ClampedArray(width * height * 4),
                colorSpace: 'srgb',
            } as ImageData;
        }),
    } as unknown as CanvasRenderingContext2D;
};

const mockCanvasCreation = (contexts: Array<CanvasRenderingContext2D | null>) => {
    const originalCreateElement = document.createElement.bind(document);

    return rs.spyOn(document, 'createElement').mockImplementation(((tagName: string) => {
        if (tagName !== 'canvas') {
            return originalCreateElement(tagName as keyof HTMLElementTagNameMap);
        }

        const context = contexts.shift() ?? null;
        return {
            width: 0,
            height: 0,
            getContext: rs.fn(() => context),
        } as unknown as HTMLCanvasElement;
    }) as typeof document.createElement);
};

afterEach(() => {
    rs.restoreAllMocks();
});

describe('projectPointOnLine', () => {
    it('returns undefined when the segment endpoints coincide', () => {
        const point = { x: 10, y: 10 };

        expect(projectPointOnLine([point, { ...point }], point)).toBeUndefined();
    });

    it('projects onto a non-zero-length segment', () => {
        const start = { x: 0, y: 0 };
        const end = { x: 10, y: 10 };

        expect(projectPointOnLine([start, end], { x: 10, y: 0 })).toEqual({ x: 5, y: 5 });
    });
});

describe('canRasteriseAtFullSize', () => {
    it('accepts the exact boundary size 16384x16384', () => {
        expect(canRasteriseAtFullSize(16384, 16384)).toBe(true);
    });

    it('rejects dimensions one pixel over the boundary', () => {
        expect(canRasteriseAtFullSize(16385, 16384)).toBe(false);
        expect(canRasteriseAtFullSize(16384, 16385)).toBe(false);
    });
});

describe('getImageData', () => {
    it('returns 1x1 placeholder for empty images', () => {
        const imageData = getImageData(createImage(0, 0));

        expect(imageData.width).toBe(1);
        expect(imageData.height).toBe(1);
    });

    it('returns a 1x1 placeholder for oversized images', () => {
        const imageData = getImageData(createImage(19156, 15010));

        expect(imageData.width).toBe(1);
        expect(imageData.height).toBe(1);
    });

    it('rasterises images within the canvas limit at full size on a CPU-backed canvas', () => {
        const context = createCanvasContext();
        const createElementSpy = mockCanvasCreation([context]);

        const imageData = getImageData(createImage(4000, 3000));

        expect(imageData.width).toBe(4000);
        expect(imageData.height).toBe(3000);
        const canvas = createElementSpy.mock.results[0]?.value as HTMLCanvasElement;
        expect(canvas.getContext).toHaveBeenCalledWith('2d', { willReadFrequently: true });
    });

    it('returns a 1x1 placeholder when the canvas context is unavailable', () => {
        mockCanvasCreation([null]);

        const imageData = getImageData(createImage(4000, 3000));

        expect(imageData.width).toBe(1);
        expect(imageData.height).toBe(1);
    });
});

describe('loadImageData', () => {
    let fetchSpy: ReturnType<typeof rs.spyOn>;
    let decodeSpy: ReturnType<typeof rs.fn>;
    let bitmap: ImageBitmap;

    beforeEach(() => {
        // Rasterising is covered by the getImageData tests; an empty bitmap keeps the canvas out of these.
        bitmap = createImage(0, 0);
        fetchSpy = rs.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('png'));
        decodeSpy = rs.fn(async () => bitmap);
        rs.stubGlobal('createImageBitmap', decodeSpy);
    });

    afterEach(() => {
        rs.unstubAllGlobals();
    });

    it('passes the abort signal to fetch and releases the bitmap', async () => {
        const signal = new AbortController().signal;

        await loadImageData('/binary', signal);

        expect(fetchSpy).toHaveBeenCalledWith('/binary', expect.objectContaining({ signal }));
        expect(bitmap.close).toHaveBeenCalled();
    });

    it('applies EXIF orientation, like <img>', async () => {
        await loadImageData('/binary');

        expect(decodeSpy).toHaveBeenCalledWith(expect.anything(), { imageOrientation: 'from-image' });
    });

    it('rejects when the server responds with an error', async () => {
        fetchSpy.mockResolvedValue(new Response(null, { status: 404 }));

        await expect(loadImageData('/binary')).rejects.toThrow('404');
    });

    it('rejects without rasterising once aborted', async () => {
        const controller = new AbortController();
        controller.abort();

        await expect(loadImageData('/binary', controller.signal)).rejects.toThrow();
        expect(bitmap.close).toHaveBeenCalled();
    });
});
