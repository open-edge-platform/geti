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

import { screen } from '@testing-library/react';
import dayjs from 'dayjs';

import { formatJobsCreationTime } from '../../../../../../shared/utils';
import { providersRender as render } from '../../../../../../test-utils/required-providers-render';
import { TrainingProgressTask } from './training-progress-task.component';

describe('Training progress task', () => {
    it('Check if version, name and architecture are properly displayed', async () => {
        const name = 'Classification';
        const architecture = 'Some test arch';
        const creationTime = formatJobsCreationTime(dayjs().toString());

        render(<TrainingProgressTask name={name} architecture={architecture} creationTime={creationTime} />);

        expect(screen.getByText(name)).toBeInTheDocument();
        expect(screen.getByText(architecture)).toBeInTheDocument();
        expect(screen.getByText(creationTime)).toBeInTheDocument();
    });
});
