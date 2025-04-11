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

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { Annotation } from '../../core/annotations/annotation.interface';
import { ShapeType } from '../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../core/annotations/utils';
import { LABEL_BEHAVIOUR } from '../../core/labels/label.interface';
import { DOMAIN } from '../../core/projects/core.interface';
import { Task } from '../../core/projects/task.interface';
import { initialCanvasConfig } from '../../core/user-settings/utils';
import { fakeAnnotationToolContext } from '../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel, labels } from '../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImageMediaItem } from '../../test-utils/mocked-items-factory/mocked-media';
import { getMockedTask, mockedTaskContextProps } from '../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { getById, getMockedImage } from '../../test-utils/utils';
import { ProjectProvider } from '../project-details/providers/project-provider/project-provider.component';
import { AnnotatorCanvas } from './annotator-canvas.component';
import { AnnotationToolContext } from './core/annotation-tool-context.interface';
import { AnnotationThresholdProvider } from './providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { useAnnotatorCanvasSettings } from './providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import {
    ExplanationOpacityProvider,
    PredictionContextProps,
    usePrediction,
} from './providers/prediction-provider/prediction-provider.component';
import { useROI } from './providers/region-of-interest-provider/region-of-interest-provider.component';
import { SelectedMediaItemProvider } from './providers/selected-media-item-provider/selected-media-item-provider.component';
import { useTaskChain } from './providers/task-chain-provider/task-chain-provider.component';
import { useTask } from './providers/task-provider/task-provider.component';
import { useZoom } from './zoom/zoom-provider.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useSearchParams: jest.fn(() => [new URLSearchParams()]),
}));

jest.mock('./providers/task-chain-provider/task-chain-provider.component', () => ({
    useTaskChain: jest.fn(),
}));

jest.mock('./providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('./providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        isTaskChainDomainSelected: () => false,
    })),
}));

jest.mock('./zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(),
}));

jest.mock('./hooks/use-annotator-scene-interaction-state.hook', () => ({
    useIsSceneBusy: jest.fn(() => false),
}));

jest.mock('../../notification/notification.component', () => ({
    ...jest.requireActual('../../notification/notification.component'),
    useNotification: jest.fn(() => ({
        addNotification: jest.fn(),
    })),
}));

jest.mock('./providers/prediction-provider/prediction-provider.component', () => ({
    ...jest.requireActual('./providers/prediction-provider/prediction-provider.component'),
    usePrediction: jest.fn(),
}));

jest.mock('./components/video-player/streaming-video-player/streaming-video-player-provider.component', () => ({
    ...jest.requireActual('./components/video-player/streaming-video-player/streaming-video-player-provider.component'),
    useStreamingVideoPlayer: jest.fn(() => ({
        isPlaying: false,
    })),
}));

jest.mock('./providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component', () => ({
    ...jest.requireActual(
        './providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component'
    ),
    useAnnotatorCanvasSettings: jest.fn(() => ({
        canvasSettingsState: [{}, jest.fn()],
        handleSaveConfig: jest.fn(),
    })),
}));

const mockROI = { x: 0, y: 0, width: 100, height: 100 };
const mockImage = getMockedImage(mockROI);

jest.mock('./providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('./components/explanation/use-inference-image.hook', () => ({
    ...jest.requireActual('./components/explanation/use-inference-image.hook'),
    useInferenceImage: jest.fn(),
}));

describe('Annotator canvas', (): void => {
    const usePredictionConfig = {
        explanations: [],
        isExplanationVisible: false,
        explanationOpacity: 50,
        selectedExplanation: {
            id: '1',
            labelsId: '1',
            name: 'Test name',
            url: 'https://fakeimage.url/',
            roi: {
                id: '123',
                shape: {
                    y: 0,
                    x: 0,
                    type: 'RECTANGLE',
                    height: 0,
                    width: 0,
                },
            },
        },
        predictionAnnotations: [],
    } as unknown as PredictionContextProps;
    const annotations: Annotation[] = [
        {
            id: 'rect-1',
            zIndex: 0,
            labels: [labelFromUser(labels[0]), labelFromUser(labels[1]), labelFromUser(labels[3])],
            shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 10, height: 10 },
            isSelected: false,
            isHidden: false,
            isLocked: false,
        },
        {
            id: 'rect-2',
            zIndex: 1,
            labels: [labelFromUser(labels[0])],
            shape: { shapeType: ShapeType.Rect, x: 30, y: 30, width: 10, height: 10 },
            isSelected: false,
            isHidden: false,
            isLocked: false,
        },
    ];

    const renderApp = async (annotationToolContext: AnnotationToolContext) => {
        const selectedMediaItem = getMockedImageMediaItem({});

        const response = render(
            <ProjectProvider
                projectIdentifier={{
                    projectId: 'project-id',
                    workspaceId: 'workspace-id',
                    organizationId: 'organization-id',
                }}
            >
                <SelectedMediaItemProvider>
                    <ExplanationOpacityProvider>
                        <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                            <AnnotatorCanvas
                                annotationToolContext={annotationToolContext}
                                selectedMediaItem={selectedMediaItem}
                                canEditAnnotationLabel
                            />
                        </AnnotationThresholdProvider>
                    </ExplanationOpacityProvider>
                </SelectedMediaItemProvider>
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        return response;
    };

    beforeEach(() => {
        (useZoom as jest.Mock).mockImplementation(() => ({
            setZoomTarget: jest.fn(),
            zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } },
        }));

        jest.mocked(useTaskChain).mockImplementation(() => ({
            inputs: [],
            outputs: annotations,
        }));

        jest.mocked(usePrediction).mockImplementation(() => usePredictionConfig);

        (useAnnotatorCanvasSettings as jest.Mock).mockImplementation(() => ({
            canvasSettingsState: [initialCanvasConfig, jest.fn()],
            handleSaveConfig: jest.fn(),
        }));
    });

    it('renders the annotator canvas', async () => {
        const tasks = [getMockedTask({ domain: DOMAIN.SEGMENTATION })];
        jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks }));

        const annotationToolContext = fakeAnnotationToolContext({ annotations });

        const { container } = await renderApp(annotationToolContext);

        const image = container.querySelector('canvas');
        expect(image).toHaveAttribute('id', 'image-test-image');

        const canvasAnnotations = screen.getByLabelText('annotations').querySelectorAll('rect, circle, polygon');
        expect(canvasAnnotations).toHaveLength(annotationToolContext.scene.annotations.length);

        expect(screen.getAllByLabelText('labels')).toHaveLength(annotationToolContext.scene.annotations.length);
    });

    it('does not show annotation tools for a classification task', async () => {
        const tasks: Task[] = [getMockedTask({ labels, domain: DOMAIN.CLASSIFICATION })];
        const selectedTask = tasks[0];
        jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks, selectedTask }));

        const annotationToolContext = fakeAnnotationToolContext({
            annotations: [{ ...annotations[0], isSelected: true }],
        });

        jest.mocked(useTaskChain).mockImplementation(() => ({
            inputs: [],
            outputs: annotationToolContext.scene.annotations,
        }));

        await renderApp(annotationToolContext);

        expect(screen.queryByRole('editor')).not.toBeInTheDocument();

        // The annotation's labels are shown
        expect(screen.getByText(labels[0].name)).toBeInTheDocument();
        expect(screen.getByText(labels[1].name)).toBeInTheDocument();
        expect(screen.getByText(labels[3].name)).toBeInTheDocument();
    });

    it('does not show annotation tools for a anomaly classification', async () => {
        const tasks: Task[] = [getMockedTask({ labels, domain: DOMAIN.ANOMALY_CLASSIFICATION })];
        const selectedTask = tasks[0];
        jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks, selectedTask }));

        const annotationToolContext = fakeAnnotationToolContext({
            annotations: [{ ...annotations[0], isSelected: true }],
        });

        jest.mocked(useTaskChain).mockImplementation(() => ({
            inputs: [],
            outputs: annotationToolContext.scene.annotations,
        }));

        await renderApp(annotationToolContext);

        expect(screen.queryByRole('editor')).not.toBeInTheDocument();

        // The annotation's labels are shown
        expect(screen.getByText(labels[0].name)).toBeInTheDocument();
        expect(screen.getByText(labels[1].name)).toBeInTheDocument();
        expect(screen.getByText(labels[3].name)).toBeInTheDocument();
    });

    it('hides the shapes of global annotations', async () => {
        const emptyLabel = getMockedLabel({
            name: 'Empty',
            behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.EXCLUSIVE,
        });
        const tasks: Task[] = [getMockedTask({ domain: DOMAIN.SEGMENTATION, labels: [emptyLabel] })];
        const selectedTask = tasks[0];
        const roi = { x: 0, y: 0, width: 1000, height: 1000 };

        jest.mocked(useROI).mockReturnValue({ roi, image: getMockedImage(roi) });

        const annotationId = 'test-annotation';
        const annotationToolContext = fakeAnnotationToolContext({
            annotations: [
                getMockedAnnotation({
                    id: annotationId,
                    labels: [labelFromUser(emptyLabel)],
                    shape: { shapeType: ShapeType.Rect, ...roi },
                    isSelected: false,
                }),
            ],
        });

        jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks, selectedTask }));

        jest.mocked(useTaskChain).mockImplementation(() => ({
            inputs: [],
            outputs: annotationToolContext.scene.annotations,
        }));

        const { container } = await renderApp(annotationToolContext);
        expect(getById(container, `annotations-canvas-${annotationId}-shape`)).toBeNull();
    });

    it('allows the user to hide labels', async () => {
        (useAnnotatorCanvasSettings as jest.Mock).mockImplementation(() => ({
            canvasSettingsState: [
                { ...initialCanvasConfig, hideLabels: { value: true, defaultValue: false } },
                jest.fn(),
            ],
            handleSaveConfig: jest.fn(),
        }));
        const tasks = [getMockedTask({ domain: DOMAIN.SEGMENTATION })];
        const annotationToolContext = fakeAnnotationToolContext({ annotations });

        jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks }));
        await renderApp(annotationToolContext);

        const canvasAnnotations = screen.getByLabelText('annotations').querySelectorAll('rect, circle, polygon');
        expect(canvasAnnotations).toHaveLength(annotationToolContext.scene.annotations.length);
        expect(screen.queryAllByLabelText('labels')).toHaveLength(0);
    });

    describe("Showing a mask for a task's input", () => {
        const domains = [
            DOMAIN.CLASSIFICATION,
            DOMAIN.DETECTION,
            DOMAIN.SEGMENTATION,
            DOMAIN.ANOMALY_CLASSIFICATION,
            DOMAIN.ANOMALY_DETECTION,
            DOMAIN.ANOMALY_SEGMENTATION,
        ];

        it.each(domains)('does not show a mask for single %o task projects', async (domain) => {
            const tasks = [getMockedTask({ id: 'task', domain })];
            const selectedTask = tasks[0];

            jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks, selectedTask }));

            const annotationToolContext = fakeAnnotationToolContext({ annotations });
            await renderApp(annotationToolContext);

            expect(screen.queryByLabelText(/Annotation mask/i)).not.toBeInTheDocument();
        });

        it('does not shows a mask for when the no task is selected', async () => {
            const tasks = [
                getMockedTask({ id: 'detection', domain: DOMAIN.DETECTION }),
                getMockedTask({ id: 'second-task', domain: DOMAIN.CLASSIFICATION }),
            ];

            const annotationToolContext = fakeAnnotationToolContext({ annotations });
            jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks, selectedTask: null }));
            await renderApp(annotationToolContext);

            expect(screen.queryByLabelText(/Annotation mask/i)).not.toBeInTheDocument();
        });

        it('does not shows a mask for when the the first task is selected', async () => {
            const tasks = [
                getMockedTask({ id: 'detection', domain: DOMAIN.DETECTION }),
                getMockedTask({ id: 'second-task', domain: DOMAIN.CLASSIFICATION }),
            ];
            const annotationToolContext = fakeAnnotationToolContext({ annotations });
            jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks, selectedTask: tasks[0] }));

            await renderApp(annotationToolContext);

            expect(screen.queryByLabelText(/Annotation mask/i)).not.toBeInTheDocument();
        });

        it.each(domains)(
            'shows a mask for when the second task %o in a task chain project is selected',
            async (domain) => {
                const tasks = [
                    getMockedTask({ id: 'detection', domain: DOMAIN.DETECTION }),
                    getMockedTask({ id: 'second-task', domain }),
                ];

                const annotationToolContext = fakeAnnotationToolContext({ annotations });
                jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks, selectedTask: tasks[1] }));

                await renderApp(annotationToolContext);

                expect(screen.getByLabelText(/Annotation mask/i)).toBeInTheDocument();
            }
        );
    });
});
