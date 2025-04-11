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

import { Tag } from './tag.component';

describe('Tag', () => {
    it('render with a dot by default', () => {
        render(<Tag text='test tag' id='test-id' />);

        expect(screen.getByTestId('test-id').children).toHaveLength(2);
    });

    it('render without a dot correctly', () => {
        render(<Tag text='test tag' withDot={false} id='test-id' />);

        expect(screen.getByTestId('test-id').children).toHaveLength(1);
    });

    it('render with a prefix if provided', () => {
        render(<Tag text='test tag' prefix={<div>Fake icon</div>} />);

        expect(screen.getByText('Fake icon')).toBeInTheDocument();
    });

    it('render with a suffix if provided', () => {
        render(<Tag text='test tag' suffix={<div>Fake icon</div>} />);

        expect(screen.getByText('Fake icon')).toBeInTheDocument();
    });
});
