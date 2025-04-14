// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedImageMediaItem, getMockedVideoFrameMediaItem } from '../test-utils/mocked-items-factory/mocked-media';
import { mockFile } from '../test-utils/mockFile';
import {
    defineMediaType,
    downloadMediaItem,
    getVideoDimensionErrors,
    isTiffFormat,
    isValidFileExtension,
    isVideoFile,
    loadImageFromFile,
    loadVideoFromFile,
    MEDIA_FILE_TYPE,
    VALID_IMAGE_TYPES,
    VALID_VIDEO_TYPES,
    VALIDATION_MESSAGES,
    VALIDATION_RULES,
} from './media-utils';
import { downloadFile } from './utils';

jest.mock('./utils', () => ({
    ...jest.requireActual('./utils'),
    downloadFile: jest.fn(),
}));

const mockImageExecutionCallback = (name: keyof FileReader, message = '') => {
    jest.spyOn(global, 'FileReader').mockImplementation(function (this: FileReader) {
        this.readAsDataURL = () => {
            // @ts-expect-error We don't care about typing "this"
            this[name](message);
        };

        return this;
    });
};

const mockVideoExecutionCallback = (name: keyof HTMLVideoElement, message = '') => {
    Object.defineProperty(global.HTMLVideoElement.prototype, 'src', {
        configurable: true,
        set() {
            this[name](message);
        },
    });
};

describe('Check media item download', () => {
    const mockedDownloadFile = jest.fn();
    beforeAll(() => {
        jest.mocked(downloadFile).mockImplementation(mockedDownloadFile);
    });

    it('Image download - should download item from src', () => {
        downloadMediaItem(getMockedImageMediaItem({ name: 'Test image', src: '/v1/media/image/image-id' }));

        expect(mockedDownloadFile).toBeCalledWith('/v1/media/image/image-id', 'Test image');
    });

    it('Image download - should replace all "." in the file name', () => {
        downloadMediaItem(getMockedImageMediaItem({ name: 'Test.image', src: '/v1/media/image/image-id' }));

        expect(mockedDownloadFile).toBeCalledWith('/v1/media/image/image-id', 'Test_image');

        downloadMediaItem(
            getMockedImageMediaItem({ name: 'Test.image.wow.lots.of.points', src: '/v1/media/image/image-id' })
        );

        expect(mockedDownloadFile).toBeCalledWith('/v1/media/image/image-id', 'Test_image_wow_lots_of_points');
    });

    it('VideoFrame download - should download full video', () => {
        downloadMediaItem(
            getMockedVideoFrameMediaItem({
                name: 'Test frame file',
                src: '/v1/media/video/video-id/frames/0/display/full',
            })
        );

        expect(mockedDownloadFile).toBeCalledWith('/v1/media/video/video-id/display/stream', 'Test frame file');
    });

    it('VideoFrame download - not proper url - should download item from src', () => {
        downloadMediaItem(
            getMockedVideoFrameMediaItem({
                name: 'Test frame file',
                src: '/v1/media/video/video-id/something_wrong/0/display/full',
            })
        );

        expect(mockedDownloadFile).toBeCalledWith(
            '/v1/media/video/video-id/something_wrong/0/display/full',
            'Test frame file'
        );
    });
});

describe('loadImageFromFile', () => {
    beforeAll(() => {
        global.URL.createObjectURL = jest.fn();
        global.URL.revokeObjectURL = jest.fn();
    });

    const mockedFile = new File([new ArrayBuffer(1)], 'file.jpg');

    it('returns a image element', () => {
        mockImageExecutionCallback('onload');

        return expect(loadImageFromFile(mockedFile)).resolves.toBeInstanceOf(HTMLImageElement);
    });

    it('returns an error', () => {
        const errorMessage = 'error message';
        mockImageExecutionCallback('onerror', errorMessage);

        return expect(loadImageFromFile(mockedFile)).rejects.toBe(errorMessage);
    });
});
describe('loadVideoFromFile', () => {
    beforeAll(() => {
        global.URL.createObjectURL = jest.fn();
        global.URL.revokeObjectURL = jest.fn();
    });

    const mockedFile = new File([new ArrayBuffer(1)], 'file.jpg');

    it('returns a video element', () => {
        mockVideoExecutionCallback('onloadstart');

        return expect(loadVideoFromFile(mockedFile)).resolves.toBeInstanceOf(HTMLVideoElement);
    });

    it('returns an error', () => {
        const errorMessage = 'error message';
        mockVideoExecutionCallback('onerror', errorMessage);

        return expect(loadVideoFromFile(mockedFile)).rejects.toBe(errorMessage);
    });
});

it('isValidFileExtension', () => {
    expect(isValidFileExtension(mockFile({ name: 'test.zip' }), ['zip'])).toBe(true);
    expect(isValidFileExtension(mockFile({ name: 'test.3gp' }), ['mp4'])).toBe(false);
});

describe('defineMediaType', () => {
    it('returns "unknown" if the file has no type', () => {
        const file = mockFile({ type: '' });

        expect(defineMediaType(file)).toEqual(MEDIA_FILE_TYPE.UNKNOWN);
    });

    it('returns "unknown" if the file has an unknown type', () => {
        const fileOne = mockFile({ type: 'y' });

        expect(defineMediaType(fileOne)).toEqual(MEDIA_FILE_TYPE.UNKNOWN);

        const fileTwo = mockFile({ type: 'txt' });

        expect(defineMediaType(fileTwo)).toEqual(MEDIA_FILE_TYPE.UNKNOWN);

        const filethree = mockFile({ type: '7z' });

        expect(defineMediaType(filethree)).toEqual(MEDIA_FILE_TYPE.UNKNOWN);
    });

    it('returns correct enum if the file is of image type', () => {
        VALID_IMAGE_TYPES.forEach((validImageType) => {
            const file = mockFile({ type: validImageType });

            expect(defineMediaType(file)).toEqual(MEDIA_FILE_TYPE.IMAGE);
        });
    });

    it('returns correct enum if the file has no type', () => {
        VALID_VIDEO_TYPES.forEach((validVideoType) => {
            const file = mockFile({ type: validVideoType });

            expect(defineMediaType(file)).toEqual(MEDIA_FILE_TYPE.VIDEO);
        });
    });
});

it('isVideoFile', () => {
    expect(isVideoFile(mockFile({ type: 'video/mp4' }))).toBe(true);
    expect(isVideoFile(mockFile({ type: 'image/jpg' }))).toBe(false);
});

it('isTiffFormat', () => {
    expect(isTiffFormat(mockFile({ name: 'test.tif' }))).toBe(true);
    expect(isTiffFormat(mockFile({ type: 'image/tiff' }))).toBe(true);
    expect(isTiffFormat(mockFile({ type: 'video/mp4' }))).toBe(false);
    expect(isTiffFormat(mockFile({ type: 'image/jpg' }))).toBe(false);
});

it('getVideoDimensionErrors', () => {
    expect(getVideoDimensionErrors({ videoWidth: VALIDATION_RULES.MIN_WIDTH - 1 } as HTMLVideoElement)).toEqual([
        VALIDATION_MESSAGES.VIDEO.MIN_WIDTH,
    ]);
    expect(getVideoDimensionErrors({ videoWidth: VALIDATION_RULES.VIDEO.MAX_WIDTH + 1 } as HTMLVideoElement)).toEqual([
        VALIDATION_MESSAGES.VIDEO.MAX_WIDTH,
    ]);
    expect(getVideoDimensionErrors({ videoHeight: VALIDATION_RULES.MIN_HEIGHT - 1 } as HTMLVideoElement)).toEqual([
        VALIDATION_MESSAGES.VIDEO.MIN_HEIGHT,
    ]);
    expect(getVideoDimensionErrors({ videoHeight: VALIDATION_RULES.VIDEO.MAX_HEIGHT + 1 } as HTMLVideoElement)).toEqual(
        [VALIDATION_MESSAGES.VIDEO.MAX_HEIGHT]
    );
});
