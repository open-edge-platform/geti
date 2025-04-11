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
