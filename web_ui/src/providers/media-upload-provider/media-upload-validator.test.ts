// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import {
    loadVideoFromFile,
    VALID_MEDIA_TYPES_DISPLAY,
    VALIDATION_MESSAGES,
    VALIDATION_RULES,
} from '../../shared/media-utils';
import { mockFile, mockGlobalFile, mockLoadVideoFromFile } from '../../test-utils/mockFile';
import { ValidationFailStatus } from './media-upload.interface';
import { mediaExtensionHandler, validateMedia } from './media-upload.validator';

jest.mock('../../shared/media-utils', () => ({
    ...jest.requireActual('../../shared/media-utils'),
    loadVideoFromFile: jest.fn(),
}));

describe('MediaUpload validator', () => {
    it('mediaExtensionHandler', () => {
        expect(mediaExtensionHandler(VALID_MEDIA_TYPES_DISPLAY)).toEqual(
            '.jpg, .jpeg, .bmp, .png, .jfif, .webp, .tif, .tiff, .mp4, .avi, .mkv, .mov, .webm, .m4v'
        );
    });

    describe('validateMedia', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });

        it('shows error messages with supported media types when the provided media type is not valid', async () => {
            const invalidFile = mockFile({ type: '' });

            const resultPromise = validateMedia(invalidFile);

            await expect(resultPromise).rejects.toEqual({
                errors: [VALIDATION_MESSAGES.UNSUPPORTED_MEDIA_TYPE],
                file: invalidFile,
                status: ValidationFailStatus.UNSUPPORTED_TYPE,
            });
        });

        describe('validateImage', () => {
            it('resolves early for files with .tiff format', async () => {
                const tiffFile = mockFile({ type: 'tiff' });

                const result = await validateMedia(tiffFile);

                expect(result).toEqual(tiffFile);
            });

            it('resolves normally if there are no errors with validation', async () => {
                const file = new File([new ArrayBuffer(1)], 'file.png');

                const result = await validateMedia(file);

                expect(result).toEqual(file);
            });

            it('checks the file extension correctly', async () => {
                // Create a file with the extension name uppercased
                const pngFile = new File([new ArrayBuffer(1)], 'file.PNG');

                const pngResult = await validateMedia(pngFile);

                expect(pngResult).toEqual(pngFile);
            });

            it('should fail when the maximum size is exceeded', async () => {
                jest.spyOn(global, 'File').mockImplementation(function () {
                    // @ts-expect-error We dont care about typing "this"
                    this.size = VALIDATION_RULES.MAX_SIZE + 1;

                    // @ts-expect-error We dont care about typing "this"
                    this.name = 'file.png';

                    // @ts-expect-error We dont care about typing "this"
                    return this;
                });

                const imageFile = new File([new ArrayBuffer(1)], 'file.png');

                const imageValidationResult = validateMedia(imageFile);

                await expect(imageValidationResult).rejects.toEqual({
                    errors: [VALIDATION_MESSAGES.IMAGE.MAX_SIZE],
                    file: imageFile,
                    status: ValidationFailStatus.INVALID_DIMENSIONS,
                });
            });
        });

        describe('validateVideo', () => {
            beforeAll(() => {
                global.URL.createObjectURL = jest.fn();
                global.URL.revokeObjectURL = jest.fn();
            });

            it('checks the file extension correctly', async () => {
                jest.mocked(loadVideoFromFile).mockResolvedValue(mockLoadVideoFromFile({}));

                const fileName = 'file.MOV';

                const movFile = mockGlobalFile(fileName);

                const movResult = await validateMedia(movFile);

                expect(movResult).toEqual(movFile);
            });

            it('should fail if the extension is not supported', async () => {
                jest.mocked(loadVideoFromFile).mockResolvedValue(mockLoadVideoFromFile({}));

                const fileName = 'file.flv';

                const file = mockGlobalFile(fileName);

                const movResult = validateMedia(file);

                await expect(movResult).rejects.toEqual({
                    errors: [VALIDATION_MESSAGES.UNSUPPORTED_MEDIA_TYPE],
                    file,
                    status: ValidationFailStatus.UNSUPPORTED_TYPE,
                });
            });

            it('should fail when the maximum size is exceeded', async () => {
                jest.mocked(loadVideoFromFile).mockResolvedValue(mockLoadVideoFromFile({}));

                const file = mockGlobalFile('file.mp4', VALIDATION_RULES.MAX_SIZE + 1);

                const videoResult = validateMedia(file);

                await expect(videoResult).rejects.toEqual({
                    errors: [VALIDATION_MESSAGES.VIDEO.MAX_SIZE],
                    file,
                    status: ValidationFailStatus.INVALID_DIMENSIONS,
                });
            });

            it('resolve avi files, duration validation will be processed on server side', async () => {
                jest.mocked(loadVideoFromFile).mockResolvedValue(
                    mockLoadVideoFromFile({ duration: VALIDATION_RULES.VIDEO.MAX_LENGTH + 1 })
                );

                const fileName = 'file.avi';

                const videoResult = validateMedia(mockGlobalFile(fileName));

                await expect(videoResult).resolves.toEqual({
                    name: fileName,
                    size: 1024,
                    type: expect.stringContaining('avi'),
                });
            });

            it('invalid video type', async () => {
                jest.mocked(loadVideoFromFile).mockResolvedValue(mockLoadVideoFromFile({}));

                const file = mockGlobalFile('file.3gp');
                const videoResult = validateMedia(file);

                await expect(videoResult).rejects.toEqual({
                    file,
                    status: ValidationFailStatus.UNSUPPORTED_TYPE,
                    errors: [VALIDATION_MESSAGES.UNSUPPORTED_MEDIA_TYPE],
                });
            });
        });
    });
});
