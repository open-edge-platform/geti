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

import { screen, waitForElementToBeRemoved } from '@testing-library/react';
import identity from 'lodash/identity';

import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedUserProjectSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationSceneProvider } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { AnnotationThresholdProvider } from '../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { PredictionProvider } from '../../providers/prediction-provider/prediction-provider.component';
import { SelectedMediaItemProvider } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { TaskChainProvider } from '../../providers/task-chain-provider/task-chain-provider.component';
import { getGlobalAnnotations } from '../../providers/task-chain-provider/utils';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { Layers } from './layers.component';

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    ...jest.requireActual('../../providers/region-of-interest-provider/region-of-interest-provider.component'),
    useROI: jest.fn(() => ({
        roi: {
            x: 0,
            y: 0,
            height: 100,
            width: 100,
        },
    })),
}));

jest.mock('../../providers/task-chain-provider/utils', () => ({
    ...jest.requireActual('../../providers/task-chain-provider/utils'),
    getGlobalAnnotations: jest.fn(() => []),
}));

jest.mock('../../zoom/zoom-provider.component', () => ({
    ...jest.requireActual('../../zoom/zoom-provider.component'),
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

describe('Layers', () => {
    const mockContext = fakeAnnotationToolContext({});
    const mockAnnotations = [
        getMockedAnnotation({ id: 'test-annotation-1' }),
        getMockedAnnotation({ id: 'test-annotation-2' }),
    ];

    const renderApp = () =>
        providersRender(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <AnnotationSceneProvider annotations={mockContext.scene.annotations} labels={[]}>
                    <TaskProvider>
                        <SelectedMediaItemProvider>
                            <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                                <TaskChainProvider tasks={[]} selectedTask={null} defaultLabel={null}>
                                    <PredictionProvider
                                        settings={getMockedUserProjectSettingsObject()}
                                        explanations={[]}
                                        initPredictions={[]}
                                        userAnnotationScene={mockContext.scene}
                                    >
                                        <Layers
                                            width={100}
                                            height={100}
                                            annotations={mockAnnotations}
                                            annotationToolContext={mockContext}
                                            annotationsFilter={identity}
                                        />
                                    </PredictionProvider>
                                </TaskChainProvider>
                            </AnnotationThresholdProvider>
                        </SelectedMediaItemProvider>
                    </TaskProvider>
                </AnnotationSceneProvider>
            </ProjectProvider>
        );

    it('renders annotation shapes', async () => {
        jest.mocked(getGlobalAnnotations).mockReturnValueOnce([]);
        renderApp();

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.queryByLabelText(`annotations-canvas-${mockAnnotations[0].id}-shape`)).toBeInTheDocument();
        expect(screen.queryByLabelText(`annotations-canvas-${mockAnnotations[1].id}-shape`)).toBeInTheDocument();
    });

    it('do not render global annotations shapes', async () => {
        jest.mocked(getGlobalAnnotations).mockReturnValue([mockAnnotations[0]]);
        renderApp();

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.queryByLabelText(`annotations-canvas-${mockAnnotations[0].id}-shape`)).not.toBeInTheDocument();
        expect(screen.queryByLabelText(`annotations-canvas-${mockAnnotations[1].id}-shape`)).toBeInTheDocument();
    });
});
