// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render } from '@testing-library/react';

import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getById } from '../../../../test-utils/utils';
import { TaskChainTemplate } from './task-chain-template.component';
import { taskChainSubDomains } from './utils';

describe('chain template', () => {
    const setSelectedDomains = jest.fn();

    it('When single domain is selected it should select the first available task-chain domain option', () => {
        render(
            <TaskChainTemplate
                selectedDomains={[DOMAIN.SEGMENTATION]}
                subDomains={taskChainSubDomains}
                setSelectedDomains={setSelectedDomains}
            />
        );

        expect(setSelectedDomains).toHaveBeenCalledWith(
            [DOMAIN.DETECTION, DOMAIN.CLASSIFICATION],
            [LabelsRelationType.SINGLE_SELECTION, LabelsRelationType.MIXED]
        );
    });

    it('Detection > Segmentation should be selected', () => {
        const { container } = render(
            <TaskChainTemplate
                subDomains={taskChainSubDomains}
                selectedDomains={[DOMAIN.DETECTION, DOMAIN.SEGMENTATION]}
                setSelectedDomains={setSelectedDomains}
            />
        );

        const detectionSegmentationWell = getById(container, 'project-creation-detection-segmentation-chain');

        expect(detectionSegmentationWell).toBeInTheDocument();
        expect(detectionSegmentationWell).toHaveClass('selected');
    });

    it('Clicking on Detection => Segmentation option should select it', () => {
        const { container } = render(
            <TaskChainTemplate
                subDomains={taskChainSubDomains}
                selectedDomains={[DOMAIN.DETECTION]}
                setSelectedDomains={setSelectedDomains}
            />
        );

        const detectionSegmentationWell = getById(container, 'project-creation-detection-segmentation-chain');
        expect(detectionSegmentationWell).toBeInTheDocument();

        detectionSegmentationWell && fireEvent.click(detectionSegmentationWell);

        expect(setSelectedDomains).toHaveBeenCalledWith(
            [DOMAIN.DETECTION, DOMAIN.CLASSIFICATION],
            [LabelsRelationType.SINGLE_SELECTION, LabelsRelationType.MIXED]
        );
    });
});
