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

import { screen } from '@testing-library/dom';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { JobsListItemMetadata, JobsListItemMetadataProps } from './jobs-list-item-metadata.component';

describe('jobs list item metadata', (): void => {
    const defaultProps: JobsListItemMetadataProps = {
        jobId: 'TestJobId',
        projectName: 'TestProjectName',
        creationTime: '2023-08-10T06:17:43.849000+00:00',
    };

    const componentRender = (props: Partial<JobsListItemMetadataProps> = {}): void => {
        render(<JobsListItemMetadata {...defaultProps} {...props} />);
    };

    it('should properly render base component', (): void => {
        componentRender();
        expect(screen.getByText('Project: TestProjectName')).toBeInTheDocument();
        expect(screen.getByText('Created: 06:17:43, 10 Aug 23')).toBeInTheDocument();

        expect(screen.queryByText('Task:')).not.toBeInTheDocument();
        expect(screen.queryByText('Precision:')).not.toBeInTheDocument();
        expect(screen.queryByText('Architecture:')).not.toBeInTheDocument();
        expect(screen.queryByText('Optimization type:')).not.toBeInTheDocument();
    });

    it('should render "Task" if it explicitly defined in props', (): void => {
        componentRender({ stepName: 'TestStepName' });
        expect(screen.getByText('Project: TestProjectName')).toBeInTheDocument();
        expect(screen.getByText('Created: 06:17:43, 10 Aug 23')).toBeInTheDocument();
        expect(screen.getByText('Task: TestStepName')).toBeInTheDocument();

        expect(screen.queryByText('Precision:')).not.toBeInTheDocument();
        expect(screen.queryByText('Architecture:')).not.toBeInTheDocument();
        expect(screen.queryByText('Optimization type:')).not.toBeInTheDocument();
    });

    it('should not render "Task" if the "Precision" defined in props', (): void => {
        componentRender({ stepName: 'TestStepName', precision: 'FP32' });
        expect(screen.getByText('Project: TestProjectName')).toBeInTheDocument();
        expect(screen.getByText('Created: 06:17:43, 10 Aug 23')).toBeInTheDocument();
        expect(screen.getByText('Precision: FP32')).toBeInTheDocument();

        expect(screen.queryByText('Task:')).not.toBeInTheDocument();
        expect(screen.queryByText('Architecture:')).not.toBeInTheDocument();
        expect(screen.queryByText('Optimization type:')).not.toBeInTheDocument();
    });

    it('should render "Architecture" if it explicitly defined in props', (): void => {
        componentRender({ stepName: 'TestStepName', precision: 'FP32', architecture: 'EfficientNet-B0' });
        expect(screen.getByText('Project: TestProjectName')).toBeInTheDocument();
        expect(screen.getByText('Created: 06:17:43, 10 Aug 23')).toBeInTheDocument();
        expect(screen.getByText('Precision: FP32')).toBeInTheDocument();
        expect(screen.getByText('Architecture: EfficientNet-B0')).toBeInTheDocument();

        expect(screen.queryByText('Task:')).not.toBeInTheDocument();
        expect(screen.queryByText('Optimization type:')).not.toBeInTheDocument();
    });

    it('should render "Optimization type" if it explicitly defined in props', (): void => {
        componentRender({
            stepName: 'TestStepName',
            precision: 'FP32',
            architecture: 'EfficientNet-B0',
            optimizationType: 'MO',
        });

        expect(screen.getByText('Project: TestProjectName')).toBeInTheDocument();
        expect(screen.getByText('Created: 06:17:43, 10 Aug 23')).toBeInTheDocument();
        expect(screen.getByText('Precision: FP32')).toBeInTheDocument();
        expect(screen.getByText('Architecture: EfficientNet-B0')).toBeInTheDocument();
        expect(screen.getByText('Optimization type: MO')).toBeInTheDocument();

        expect(screen.queryByText('Task:')).not.toBeInTheDocument();
    });

    it('should render "Cost" if it explicitly defined in props', (): void => {
        componentRender({
            projectName: 'Test project',
            cost: {
                requested: 20,
                consumed: 10,
            },
        });

        expect(screen.getByText('Cost: 20 credits')).toBeVisible();
    });
});
