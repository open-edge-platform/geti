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

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { labelFromModel, labelFromUser } from '../../../../core/annotations/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import {
    getMockedDatasetIdentifier,
    getMockedProjectIdentifier,
} from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedUserProjectSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedTask, mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationSceneProvider } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { AnnotationThresholdProvider } from '../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { AnnotationToolProvider } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import {
    PredictionProvider,
    useExplanationOpacity,
} from '../../providers/prediction-provider/prediction-provider.component';
import { SelectedMediaItemProvider } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { TaskChainProvider } from '../../providers/task-chain-provider/task-chain-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { AnnotatorProviders } from '../../test-utils/annotator-render';
import { ZoomProvider } from '../../zoom/zoom-provider.component';
import { PreviewCanvasContent } from './preview-canvas-content.component';

jest.mock('../../providers/prediction-provider/prediction-provider.component', () => ({
    ...jest.requireActual('../../providers/prediction-provider/prediction-provider.component'),
    useExplanationOpacity: jest.fn(),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

describe('PreviewCanvasContent', () => {
    const mockAnnotation = getMockedAnnotation({
        id: 'annotation-1',
        labels: [labelFromUser(getMockedLabel({ id: '123', name: 'annotation-label' }), 'userId-test')],
    });
    const mockPrediction = getMockedAnnotation({
        id: 'prediction-1',
        labels: [
            labelFromModel(
                getMockedLabel({ id: '321', name: 'prediction-label' }),
                0.01,
                'modelId-test',
                'modelStorageId-test'
            ),
        ],
    });

    const renderApp = async ({
        tasks = [],
        selectedTask = null,
        isPredictionMode,
        showOverlapAnnotations = false,
    }: {
        tasks?: Task[];
        selectedTask?: Task | null;
        isPredictionMode: boolean;
        showOverlapAnnotations?: boolean;
    }) => {
        jest.mocked(useExplanationOpacity).mockReturnValue({
            showOverlapAnnotations,
            explanationOpacity: 0,
            setShowOverlapAnnotations: jest.fn(),
            setExplanationOpacity: jest.fn(),
        });

        jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks, selectedTask }));

        const mockContext = fakeAnnotationToolContext({ annotations: [mockAnnotation] });

        providersRender(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <AnnotationSceneProvider annotations={mockContext.scene.annotations} labels={[]}>
                    <SelectedMediaItemProvider>
                        <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                            <TaskChainProvider tasks={[]} selectedTask={null} defaultLabel={null}>
                                <PredictionProvider
                                    settings={getMockedUserProjectSettingsObject()}
                                    explanations={[]}
                                    initPredictions={[mockPrediction]}
                                    userAnnotationScene={mockContext.scene}
                                >
                                    <AnnotatorProviders
                                        datasetIdentifier={getMockedDatasetIdentifier({
                                            workspaceId: 'workspace-id',
                                            projectId: 'project-id',
                                            datasetId: 'in-memory-dataset',
                                        })}
                                    >
                                        <ZoomProvider>
                                            <AnnotationToolProvider>
                                                <PreviewCanvasContent
                                                    annotations={[mockAnnotation]}
                                                    predictions={[mockPrediction]}
                                                    isPredictionMode={isPredictionMode}
                                                    selectedMediaItem={getMockedImageMediaItem({})}
                                                />
                                            </AnnotationToolProvider>
                                        </ZoomProvider>
                                    </AnnotatorProviders>
                                </PredictionProvider>
                            </TaskChainProvider>
                        </AnnotationThresholdProvider>
                    </SelectedMediaItemProvider>
                </AnnotationSceneProvider>
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    describe('prediction mode', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });

        it('predictions are visible', async () => {
            await renderApp({ isPredictionMode: true });

            expect(screen.queryByText(mockAnnotation.labels[0].name)).not.toBeInTheDocument();
            expect(screen.queryByLabelText(`Not selected shape ${mockAnnotation.id}`)).not.toBeInTheDocument();

            expect(screen.getByText(mockPrediction.labels[0].name)).toBeVisible();
            expect(screen.getByLabelText(`Not selected shape ${mockPrediction.id}`)).toBeVisible();
        });

        it('annotations and predictions are visible', async () => {
            await renderApp({ isPredictionMode: true, showOverlapAnnotations: true });

            expect(screen.getByText(mockAnnotation.labels[0].name)).toBeVisible();
            expect(screen.getByLabelText(`Not selected shape ${mockAnnotation.id}`)).toBeVisible();

            expect(screen.getByText(mockPrediction.labels[0].name)).toBeVisible();
            expect(screen.getByLabelText(`Not selected shape ${mockPrediction.id}`)).toBeVisible();
        });

        it('classification task: hide predictions when "showOverlapAnnotations" is true', async () => {
            const classificationTask = getMockedTask({
                domain: DOMAIN.CLASSIFICATION,
                labels: [...mockAnnotation.labels],
            });

            await renderApp({
                isPredictionMode: true,
                showOverlapAnnotations: true,
                tasks: [classificationTask],
                selectedTask: classificationTask,
            });

            expect(screen.getByText(mockAnnotation.labels[0].name)).toBeVisible();
            expect(screen.getByLabelText(`Not selected shape ${mockAnnotation.id}`)).toBeVisible();

            expect(screen.queryByText(mockPrediction.labels[0].name)).not.toBeInTheDocument();
            expect(screen.queryByLabelText(`Not selected shape ${mockPrediction.id}`)).not.toBeInTheDocument();
        });
    });

    describe('annotation mode', () => {
        it('annotations are visible', async () => {
            await renderApp({ isPredictionMode: false });

            expect(screen.queryByText(mockPrediction.labels[0].name)).not.toBeInTheDocument();
            expect(screen.queryByLabelText(`Not selected shape ${mockPrediction.id}`)).not.toBeInTheDocument();

            expect(screen.getByText(mockAnnotation.labels[0].name)).toBeVisible();
            expect(screen.getByLabelText(`Not selected shape ${mockAnnotation.id}`)).toBeVisible();
        });
    });
});
