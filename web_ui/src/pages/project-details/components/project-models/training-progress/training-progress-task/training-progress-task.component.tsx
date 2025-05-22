// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Grid, repeat } from '@geti/ui';

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
