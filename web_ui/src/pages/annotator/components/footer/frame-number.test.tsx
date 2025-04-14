// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { getMockedVideoFrameMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { FrameNumber } from './frame-number.component';

describe('Frame number', () => {
    it('Check if there is frame number (78) shown properly', () => {
        render(
            <FrameNumber
                mediaItem={getMockedVideoFrameMediaItem({
                    identifier: { videoId: '123', frameNumber: 78, type: MEDIA_TYPE.VIDEO_FRAME },
                })}
            />
        );

        expect(screen.getByText('78F')).toBeInTheDocument();
    });
});
