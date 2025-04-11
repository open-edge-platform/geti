// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { render } from '@testing-library/react';

import { getMockedLabel } from '../../../../../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getById } from '../../../../../../../../../test-utils/utils';
import { Label } from './label.component';

describe('Label', () => {
    it('Check if label will render proper text with proper id', () => {
        const projectName = 'nametest';
        const label = getMockedLabel({
            name: 'dog',
            color: 'ededed',
            id: 'dog-id',
        });

        const { container } = render(<Label projectName={projectName} label={label} />);
        const labelElement = getById(container, `project-labels-${projectName}-label-${label.name}`);

        expect(labelElement).toHaveTextContent(label.name);
    });
});
