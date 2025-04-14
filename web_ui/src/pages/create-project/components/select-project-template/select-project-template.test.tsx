// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { projectListRender as render } from '../../../../test-utils/projects-list-providers-render';
import { getById } from '../../../../test-utils/utils';
import {
    ProjectMetadata,
    ProjectType,
    STEPS,
} from '../../new-project-dialog-provider/new-project-dialog-provider.interface';
import { SelectProjectTemplate } from './select-project-template.component';

describe('Select project template step', () => {
    const animationDirection = -1;
    const mockMetadata: ProjectMetadata = {
        name: 'test',
        selectedDomains: [DOMAIN.SEGMENTATION],
        projectTypeMetadata: [
            { domain: DOMAIN.SEGMENTATION, labels: [], relation: LabelsRelationType.SINGLE_SELECTION },
        ],
        selectedTab: 'Detection',
        currentStep: STEPS.SELECT_TEMPLATE,
        projectType: ProjectType.SINGLE,
    };

    it('Select "Detection" tab and its first element are selected by default', async () => {
        const setValidationError = jest.fn();
        const { container } = await render(
            <SelectProjectTemplate
                metadata={mockMetadata}
                updateProjectState={jest.fn()}
                animationDirection={animationDirection}
                setValidationError={setValidationError}
            />
        );

        const detectionCard = getById(container, 'detection-card-id');
        expect(detectionCard).toHaveClass('selected', { exact: false });

        expect(screen.getByRole('tab', { name: 'Detection', selected: true })).toBeInTheDocument();
        expect(setValidationError).toBeCalled();
    });

    describe('FEATURE_FLAG_ANOMALY_REDUCTION enabled', () => {
        it('should display only "Anomaly detection" card', async () => {
            const anomalyMetadata: ProjectMetadata = {
                name: 'test',
                selectedDomains: [DOMAIN.ANOMALY_DETECTION],
                projectTypeMetadata: [
                    { domain: DOMAIN.ANOMALY_DETECTION, labels: [], relation: LabelsRelationType.SINGLE_SELECTION },
                ],
                selectedTab: 'Anomaly',
                currentStep: STEPS.SELECT_TEMPLATE,
                projectType: ProjectType.SINGLE,
            };

            await render(
                <SelectProjectTemplate
                    animationDirection={animationDirection}
                    metadata={anomalyMetadata}
                    updateProjectState={jest.fn()}
                    setValidationError={jest.fn()}
                />,
                {
                    featureFlags: { FEATURE_FLAG_ANOMALY_REDUCTION: true },
                }
            );

            expect(screen.getByText('Anomaly detection')).toBeInTheDocument();
            expect(screen.getByText('Categorize images as normal or anomalous.')).toBeInTheDocument();

            expect(screen.queryByText('Anomaly classification')).not.toBeInTheDocument();
            expect(
                screen.queryByText('Detect and categorize an object as normal or anomalous.')
            ).not.toBeInTheDocument();

            expect(screen.queryByText('Anomaly segmentation')).not.toBeInTheDocument();
            expect(
                screen.queryByText('Segment and categorize an object as normal or anomalous.')
            ).not.toBeInTheDocument();
        });
    });

    describe('FEATURE_FLAG_KEYPOINT_DETECTION', () => {
        it('should have "Keypoint Detection" tab', async () => {
            await render(
                <SelectProjectTemplate
                    animationDirection={animationDirection}
                    metadata={mockMetadata}
                    updateProjectState={jest.fn()}
                    setValidationError={jest.fn()}
                />,
                { featureFlags: { FEATURE_FLAG_KEYPOINT_DETECTION: true } }
            );

            expect(screen.getByRole('tab', { name: 'Keypoint Detection' })).toBeInTheDocument();
        });

        it('"Keypoint Detection" tab should be hidden if the flag is off', async () => {
            await render(
                <SelectProjectTemplate
                    animationDirection={animationDirection}
                    metadata={mockMetadata}
                    updateProjectState={jest.fn()}
                    setValidationError={jest.fn()}
                />,
                { featureFlags: { FEATURE_FLAG_KEYPOINT_DETECTION: false } }
            );

            expect(screen.queryByRole('tab', { name: 'Keypoint Detection' })).not.toBeInTheDocument();
        });
    });
});
