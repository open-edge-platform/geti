// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
