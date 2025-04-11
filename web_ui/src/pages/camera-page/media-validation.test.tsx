// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
