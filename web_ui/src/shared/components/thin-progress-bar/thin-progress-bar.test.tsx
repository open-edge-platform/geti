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

import { render, screen } from '@testing-library/react';

import { ThinProgressBar, ThinProgressBarProps } from './thin-progress-bar.component';

describe('UploadStatusProgressBar', () => {
    it('renders an element with the correct styles based on props', () => {
        const testProps: ThinProgressBarProps = {
            progress: 0,
            size: 'size-50',
            color: 'blue-400',
            customColor: '',
            trackColor: 'gray-400',
        };

        render(<ThinProgressBar {...testProps} />);

        expect(screen.getByTestId('thin-progress-bar')).toHaveStyle({
            height: testProps.size,
            backgroundColor: testProps.color,
            width: `${testProps.progress}%`,
        });
    });
});
