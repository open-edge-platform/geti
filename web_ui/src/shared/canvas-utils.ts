// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { decode, decodeImage, toRGBA8 } from 'utif';

export const drawImageOnCanvas = (img: HTMLImageElement, filter = ''): HTMLCanvasElement => {
    const canvas: HTMLCanvasElement = document.createElement('canvas');

    canvas.width = img.naturalWidth ? img.naturalWidth : img.width;
    canvas.height = img.naturalHeight ? img.naturalHeight : img.height;

    const ctx = canvas.getContext('2d');

    if (ctx) {
        const width = img.naturalWidth ? img.naturalWidth : img.width;
        const height = img.naturalHeight ? img.naturalHeight : img.height;

        ctx.filter = filter;
        ctx.drawImage(img, 0, 0, width, height);
    }

    return canvas;
};

export const getImageData = (img: HTMLImageElement): ImageData => {
    // Always return valid imageData, even if the image isn't loaded yet.
    if (img.width === 0 && img.height === 0) {
        return new ImageData(1, 1);
    }

    const canvas = drawImageOnCanvas(img);
    const ctx = canvas.getContext('2d') as CanvasRenderingContext2D;

    const width = img.naturalWidth ? img.naturalWidth : img.width;
    const height = img.naturalHeight ? img.naturalHeight : img.height;

    return ctx.getImageData(0, 0, width, height);
};

export const getImageDataUrl = (imageData: ImageData): string => {
    const canvas = document.createElement('canvas');

    const ctx = canvas.getContext('2d');

    if (ctx) {
        ctx.putImageData(imageData, 0, 0);

        return canvas.toDataURL();
    }

    return '';
};

export const getImageDataFromTiffFile = async (file: File): Promise<ImageData> => {
    const canvas = document.createElement('canvas') as HTMLCanvasElement;

    try {
        // Get the file buffer and decode it
        const fileBuffer = await file.arrayBuffer();
        const ifds = decode(fileBuffer);

        if (ifds.length !== 0) {
            const tiff = ifds[0];

            // Decode the image and convert into RGBA format
            decodeImage(fileBuffer, tiff);

            const rgbaData = toRGBA8(tiff);

            canvas.width = tiff.width;
            canvas.height = tiff.height;

            // Create new ImageData object with decoded data
            const imageData = new ImageData(new Uint8ClampedArray(rgbaData), tiff.width, tiff.height);

            return imageData;
        }
    } catch (error) {
        console.error(error);
    }

    return new ImageData(1, 1);
};

export const getFileFromCanvas = (canvas: HTMLCanvasElement, fileName = '', type = 'image/jpeg') =>
    new Promise<File>(async (resolve, reject) => {
        canvas.toBlob((blob) => {
            blob ? resolve(new File([blob], fileName, { type })) : reject('error retrieving canvas blob file');
        }, type);
    });
