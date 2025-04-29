// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { dimensionValue } from '@react-spectrum/utils';
import { screen } from '@testing-library/react';

import { fakeAnnotationToolContext } from '../../../../../../test-utils/fake-annotator-context';
import { mockedLongLabels } from '../../../../../../test-utils/mocked-items-factory/mocked-labels';
import { projectRender } from '../../../../../../test-utils/project-provider-render';
import { AnnotationSceneProvider } from '../../../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { TaskProvider } from '../../../../providers/task-provider/task-provider.component';
import { LabelsShortcuts } from '../labels-shortcuts.component';

describe('label shortcut item', () => {
    it('Check if long label is displayed properly', async () => {
        await projectRender(
            <TaskProvider>
                <AnnotationSceneProvider annotations={[]} labels={mockedLongLabels}>
                    <LabelsShortcuts
                        labels={mockedLongLabels}
                        annotationToolContext={fakeAnnotationToolContext()}
                        isDisabled={false}
                    />
                </AnnotationSceneProvider>
            </TaskProvider>
        );

        expect(screen.getByText(mockedLongLabels[0].name)).toHaveStyle(
            `text-overflow: ellipsis; max-width: ${dimensionValue('size-2400')}`
        );
        expect(screen.getByText(mockedLongLabels[1].name)).toHaveStyle(
            `text-overflow: ellipsis; max-width: ${dimensionValue('size-2400')}`
        );
        expect(screen.getByText(mockedLongLabels[2].name)).toHaveStyle(
            `text-overflow: ellipsis; max-width: ${dimensionValue('size-2400')}`
        );
    });
});
