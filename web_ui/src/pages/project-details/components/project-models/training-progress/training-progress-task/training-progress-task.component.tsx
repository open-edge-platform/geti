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

import { ReactNode } from 'react';

import { Grid, repeat } from '@adobe/react-spectrum';

import { TrainingProgressTaskItem } from './training-progress-task-item/training-progress-task-item.component';

interface TrainingProgressTaskProps {
    name: string;
    architecture: string;
    creationTime: string;
}

interface TrainingProgressTaskItemWrapperProps {
    children: ReactNode;
}

const TrainingProgressTaskItemWrapper = ({ children }: TrainingProgressTaskItemWrapperProps) => (
    <Grid columns={['max-content', '1fr']} alignItems={'center'} gap={'size-100'} alignSelf={'start'}>
        {children}
    </Grid>
);

export const TrainingProgressTask = ({ name, architecture, creationTime }: TrainingProgressTaskProps): JSX.Element => {
    return (
        <Grid columns={repeat(2, '1fr')} rowGap={'size-100'}>
            <TrainingProgressTaskItemWrapper>
                <TrainingProgressTaskItem name={'Task'} value={name} />
            </TrainingProgressTaskItemWrapper>
            <TrainingProgressTaskItemWrapper>
                <TrainingProgressTaskItem name={'Architecture'} value={architecture} />
                <TrainingProgressTaskItem name={'Creation time'} value={creationTime} />
            </TrainingProgressTaskItemWrapper>
        </Grid>
    );
};
