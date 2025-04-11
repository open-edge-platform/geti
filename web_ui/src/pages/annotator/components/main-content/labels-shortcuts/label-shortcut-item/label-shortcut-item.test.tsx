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
