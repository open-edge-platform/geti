// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { loadVideoFromFile, VALIDATION_RULES } from '../../shared/media-utils';
import { mockFile, mockGlobalFile, mockLoadVideoFromFile } from '../../test-utils/mockFile';
import { validateMediaSize, VALIDATION_MESSAGES } from './media-validation-utils';

jest.mock('../../shared/media-utils', () => ({
    ...jest.requireActual('../../shared/media-utils'),
    loadVideoFromFile: jest.fn(),
}));

describe('useMediaValidation', () => {
    describe('validateMediaSize', () => {
        it('image size over the limit shows error message', async () => {
            const mockedImage = mockFile({ size: VALIDATION_RULES.INDEXED_DB.MAX_SIZE + 10 });

            const { message, error } = validateMediaSize(mockedImage);

            expect(message).toEqual(VALIDATION_MESSAGES.IMAGE.MAX_SIZE);
            expect(error).toEqual(true);
        });

        it('video size over the limit shows error message', async () => {
            const mockedImage = mockFile({ size: VALIDATION_RULES.INDEXED_DB.MAX_SIZE + 10, type: 'video/mp4' });

            const { message, error } = validateMediaSize(mockedImage);

            expect(message).toEqual(VALIDATION_MESSAGES.VIDEO.MAX_SIZE);
            expect(error).toEqual(true);
        });

        it('image size equal to limit calls callback', async () => {
            const mockedImage = mockFile({ size: VALIDATION_RULES.INDEXED_DB.MAX_SIZE });
            const { error } = validateMediaSize(mockedImage);

            expect(error).toEqual(false);
        });
    });

    // TOOD: unskip after we support video
    // eslint-disable-next-line jest/no-disabled-tests
    describe.skip('validateVideoDimensions', () => {
        it('video width over the limit, shows error message', async () => {
            jest.mocked(loadVideoFromFile).mockResolvedValue(
                mockLoadVideoFromFile({ videoWidth: VALIDATION_RULES.VIDEO.MAX_WIDTH + 10 })
            );

            const file = mockGlobalFile('file.mp4');

            const { message, error } = validateMediaSize(file);

            expect(message).toEqual(VALIDATION_MESSAGES.VIDEO.MAX_SIZE);
            expect(error).toEqual(true);
        });

        it('valid video calls, callback', async () => {
            jest.mocked(loadVideoFromFile).mockResolvedValue(mockLoadVideoFromFile({}));

            const file = mockGlobalFile('file.mp4');

            const { error } = validateMediaSize(file);

            expect(error).toEqual(false);
        });
    });
});
