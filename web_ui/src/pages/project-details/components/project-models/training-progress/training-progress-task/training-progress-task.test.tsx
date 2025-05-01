// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { formatJobsCreationTime } from '@shared/utils';
import { screen } from '@testing-library/react';
import dayjs from 'dayjs';

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
