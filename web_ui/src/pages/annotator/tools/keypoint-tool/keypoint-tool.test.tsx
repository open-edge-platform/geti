// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { render, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { mockedLongLabels } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { RequiredProviders } from '../../../../test-utils/required-providers-render';
import { getMockedImage, getMockedROI } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationSceneProvider } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { SelectedMediaItemProvider } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { TaskChainProvider } from '../../providers/task-chain-provider/task-chain-provider.component';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { KeypointStateProvider } from './keypoint-state-provider.component';
import { KeypointTool } from './keypoint-tool.component';

const annotationToolContext = fakeAnnotationToolContext({});

const mockROI = getMockedROI({ x: 0, y: 0, width: 3000, height: 3000 });
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('./../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

describe('KeypointTool', () => {
    const renderApp = async () => {
        render(
            <RequiredProviders>
                <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                    <TaskProvider>
                        <SelectedMediaItemProvider>
                            <AnnotationSceneProvider annotations={[]} labels={mockedLongLabels}>
                                <TaskChainProvider tasks={[]} selectedTask={null} defaultLabel={null}>
                                    <KeypointStateProvider>
                                        <KeypointTool annotationToolContext={annotationToolContext} />
                                    </KeypointStateProvider>
                                </TaskChainProvider>
                            </AnnotationSceneProvider>
                        </SelectedMediaItemProvider>
                    </TaskProvider>
                </ProjectProvider>
            </RequiredProviders>
        );
        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    // TODO: Update the tests once we have the final integration with the skeleton service
    it('render app', async () => {
        await renderApp();

        expect(screen.getAllByRole('editor').at(0)).toBeVisible();
    });
});
