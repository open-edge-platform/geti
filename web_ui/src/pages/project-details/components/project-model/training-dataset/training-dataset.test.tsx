// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { TrainingDataset } from './training-dataset.component';

jest.mock('../../../../../hooks/use-project-identifier/use-project-identifier', () => ({
    useProjectIdentifier: jest.fn(),
}));

describe('TrainingDataset component', () => {
    const projectIdentifier = getMockedProjectIdentifier({
        workspaceId: 'test-workspace',
        projectId: 'test=project',
    });
    const revisionId = 'test-revision';
    const storageId = 'test-dataset';
    const modelInformation = `Template @ architecture - Version 1 (15 Dec 2022)`;
    const taskId = 'test-task';

    beforeAll(() => {
        jest.mocked(useProjectIdentifier).mockImplementation(() => projectIdentifier);
    });

    it('Check proper icon, title and percentage is shown in 3 buckets', async () => {
        await render(
            <TrainingDataset
                revisionId={revisionId}
                storageId={storageId}
                modelInformation={modelInformation}
                modelLabels={[]}
                taskId={taskId}
                isActive={false}
            />
        );

        expect(await screen.findByTestId('training-subsets-content')).toBeInTheDocument();

        expect(screen.getByTestId('training-subset-title')).toHaveTextContent(`check-shield.svgTraining42%`);
        expect(screen.getByTestId('testing-subset-title')).toHaveTextContent(`bulb.svgTesting38%`);
        expect(screen.getByTestId('validation-subset-title')).toHaveTextContent(`document.svgValidation19%`);
    });
});
