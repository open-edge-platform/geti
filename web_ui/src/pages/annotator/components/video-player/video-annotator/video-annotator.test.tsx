// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { createInMemoryAnnotationService } from '../../../../../core/annotations/services/in-memory-annotation-service';
import { LABEL_BEHAVIOUR } from '../../../../../core/labels/label.interface';
import { isEmptyLabel } from '../../../../../core/labels/utils';
import { createInMemoryMediaService } from '../../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { ProjectProps } from '../../../../../core/projects/project.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { Task } from '../../../../../core/projects/task.interface';
import { getMockedDatasetIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel, labels as mockedLabels } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedVideoFrameMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { VideoPlayerProvider } from '../video-player-provider.component';

import './../../../../../test-utils/mock-resize-observer';

import { VideoAnnotator } from './video-annotator.component';

const mockedDatasetIdentifier = getMockedDatasetIdentifier({
    workspaceId: 'test-workspace',
    projectId: 'test-project',
    datasetId: 'test-dataset',
});

jest.mock('../../../hooks/use-dataset-identifier.hook', () => ({
    useDatasetIdentifier: jest.fn(() => {
        return mockedDatasetIdentifier;
    }),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
    useParams: jest.fn(() => ({
        projectId: 'project-id',
        workspaceId: 'workspace-id',
    })),
}));

describe('Video annotator', () => {
    const selectFrame = jest.fn();

    afterAll(() => {
        jest.clearAllMocks();
    });

    const renderVideoPlayer = async (project: ProjectProps, task: Task | null = null) => {
        const annotationService = createInMemoryAnnotationService();
        const mediaService = createInMemoryMediaService();
        const projectService = createInMemoryProjectService();

        projectService.getProject = jest.fn(async () => {
            return project;
        });

        const selectVideoFrame = jest.fn();

        const App = () => {
            return <VideoAnnotator selectFrame={selectFrame} />;
        };

        await render(
            <VideoPlayerProvider videoFrame={videoFrame} selectVideoFrame={selectVideoFrame}>
                <App />
            </VideoPlayerProvider>,
            {
                initialEntries: task !== null ? [`?task-id=${task.id}`] : undefined,
                services: { projectService, annotationService, mediaService },
            }
        );

        return { annotationService, selectVideoFrame };
    };
    const videoFrame = getMockedVideoFrameMediaItem({});

    const emptyLabel = getMockedLabel({
        name: 'Empty task label',
        group: 'Empty',
        parentLabelId: null,
        isExclusive: true,
    });
    const labels = [...mockedLabels, emptyLabel];

    describe('Labels in the video annotator', () => {
        it('render task labels', async () => {
            const project: ProjectProps = getMockedProject({
                labels,
                tasks: [getMockedTask({ id: 'classification', domain: DOMAIN.CLASSIFICATION, labels })],
            });

            await renderVideoPlayer(project);

            labels.forEach((label) => {
                if (isEmptyLabel(label)) {
                    expect(screen.queryByTestId(`video-labels-${label.id}`)).not.toBeInTheDocument();
                } else {
                    expect(screen.queryByTestId(`video-labels-${label.id}`)).toBeVisible();
                }
            });
        });

        it('shows normal and anomalous labels', async () => {
            const anomalyLabels = [
                getMockedLabel({
                    id: 'normal',
                    name: 'Normal',
                    behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.EXCLUSIVE,
                }),
                getMockedLabel({
                    id: 'anomalous',
                    name: 'Anomalous',
                    behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.ANOMALOUS,
                }),
            ];
            const project: ProjectProps = getMockedProject({
                labels: anomalyLabels,
                tasks: [
                    getMockedTask({
                        id: 'anomaly-classification',
                        domain: DOMAIN.ANOMALY_CLASSIFICATION,
                        labels: anomalyLabels,
                    }),
                ],
            });

            await renderVideoPlayer(project);

            anomalyLabels.forEach((label) => expect(screen.queryByTestId(`video-labels-${label.id}`)).toBeVisible());
        });

        it('render single keypoint label', async () => {
            const keypointLabel = getMockedLabel({ id: 'keypoint-label-id', name: 'keypoint' });
            const project: ProjectProps = getMockedProject({
                labels,
                tasks: [
                    getMockedTask({
                        id: 'classification',
                        domain: DOMAIN.KEYPOINT_DETECTION,
                        labels: [keypointLabel, ...labels],
                    }),
                ],
            });

            await renderVideoPlayer(project);

            expect(screen.queryAllByTestId(/video-labels-/)).toHaveLength(1);
            expect(screen.getByTestId(`video-labels-${keypointLabel.id}`)).toBeVisible();
        });

        describe('Task chain', () => {
            const [detectionLabel, ...classificationLabels] = mockedLabels;
            const [detectionTask, classificationTask] = [
                getMockedTask({
                    id: 'detection',
                    domain: DOMAIN.DETECTION,
                    labels: [detectionLabel],
                }),
                getMockedTask({
                    id: 'classification',
                    domain: DOMAIN.CLASSIFICATION,
                    labels: classificationLabels,
                }),
            ];

            const project: ProjectProps = getMockedProject({
                labels: mockedLabels,
                tasks: [detectionTask, classificationTask],
            });

            it('only shows labels from the selected task [detection]', async () => {
                await renderVideoPlayer(project, detectionTask);

                detectionTask.labels.forEach((label) =>
                    expect(screen.queryByTestId(`video-labels-${label.id}`)).toBeVisible()
                );

                classificationTask.labels.forEach((label) =>
                    expect(screen.queryByTestId(`video-labels-${label.id}`)).not.toBeInTheDocument()
                );
            });

            it('only shows labels from the selected task [classification]', async () => {
                await renderVideoPlayer(project, classificationTask);

                detectionTask.labels.forEach((label) =>
                    expect(screen.queryByTestId(`video-labels-${label.id}`)).not.toBeInTheDocument()
                );

                classificationTask.labels.forEach((label) =>
                    expect(screen.queryByTestId(`video-labels-${label.id}`)).toBeVisible()
                );
            });
        });
    });
});
