// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { getById } from '../../../test-utils/utils';
import { LabelColorThumb } from './label-color-thumb.component';

describe('LabelColorThumb', () => {
    it('render labels color', async () => {
        const noObjectLabel = getMockedLabel({ id: '123', color: '#000', name: 'test' });
        const { container } = render(<LabelColorThumb id={'123'} label={noObjectLabel} />);

        expect(getById(container, noObjectLabel.id)).toBeInTheDocument();
    });

    describe('empty labels', () => {
        it('No object', async () => {
            const noObjectLabel = getMockedLabel({
                id: '123',
                color: '#000',
                name: 'No object',
                group: 'No object',
                isEmpty: true,
            });
            const { container } = render(<LabelColorThumb id={'123'} label={noObjectLabel} />);

            expect(getById(container, noObjectLabel.id)).toBeNull();
        });

        it('Empty', async () => {
            const noObjectLabel = getMockedLabel({
                id: '123',
                color: '#000',
                name: 'Empty',
                group: 'Empty',
                isEmpty: true,
            });
            const { container } = render(<LabelColorThumb id={'123'} label={noObjectLabel} />);

            expect(getById(container, noObjectLabel.id)).toBeNull();
        });

        it('No class', async () => {
            const noObjectLabel = getMockedLabel({
                id: '123',
                color: '#000',
                name: 'No class',
                group: 'No class',
                isEmpty: true,
            });
            const { container } = render(<LabelColorThumb id={'123'} label={noObjectLabel} />);

            expect(getById(container, noObjectLabel.id)).toBeNull();
        });
    });
});
