// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { TransformComponent } from 'react-zoom-pan-pinch';

import { labelFromUser } from '../../../../core/annotations/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { labels as mockedLabels } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask, mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { getById } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import {
    AnnotationSceneProvider,
    useAnnotationScene,
} from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { TaskProvider, useTask } from '../../providers/task-provider/task-provider.component';
import { ZoomProvider } from '../../zoom/zoom-provider.component';
import { ActionButtons } from './action-buttons.component';

jest.mock('../../hooks/use-annotator-scene-interaction-state.hook', () => ({
    useIsSceneBusy: () => false,
}));

// Used  fitImageToScreen button
jest.mock('../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component', () => ({
    useAnnotatorCanvasSettings: () => {
        return {
            canvasSettingsState: [{}, jest.fn()],
            handleSaveConfig: jest.fn(),
        };
    },
}));
jest.mock('../../providers/annotator-provider/annotator-provider.component', () => ({
    useAnnotator: () => {
        return {
            image: { width: 100, height: 100 },
            hotKeys: {
                hideAllAnnotations: 'a',
            },
        };
    },
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({ tasks: [], selectedTask: null })),
}));

describe('Action buttons', () => {
    const App = ({ annotationToolContext }: { annotationToolContext: AnnotationToolContext }) => {
        const scene = useAnnotationScene();
        return (
            <ActionButtons
                annotationToolContext={{
                    ...annotationToolContext,
                    scene,
                }}
            />
        );
    };

    it('toggles visibility of annotations', async () => {
        const annotationToolContext = fakeAnnotationToolContext({
            annotations: [
                getMockedAnnotation({ id: '1', isHidden: false }),
                getMockedAnnotation({ id: '2', isHidden: false }),
            ],
        });

        const { container } = render(
            <ProjectProvider
                projectIdentifier={{
                    organizationId: 'organization-id',
                    workspaceId: 'workspace-id',
                    projectId: 'project-id',
                }}
            >
                <TaskProvider>
                    <AnnotationSceneProvider
                        annotations={annotationToolContext.scene.annotations}
                        labels={annotationToolContext.scene.labels}
                    >
                        <ZoomProvider>
                            <App annotationToolContext={annotationToolContext} />
                            <TransformComponent>{''}</TransformComponent>
                        </ZoomProvider>
                    </AnnotationSceneProvider>
                </TaskProvider>
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        const visibilityButton = getById(container, 'annotation-all-annotations-toggle-visibility');
        expect(visibilityButton).toBeInTheDocument();
        visibilityButton && fireEvent.click(visibilityButton);

        expect(visibilityButton).toHaveAttribute('aria-pressed', 'true');

        visibilityButton && fireEvent.click(visibilityButton);
        expect(visibilityButton).toHaveAttribute('aria-pressed', 'false');
    });

    it('toggle visibility button is disabled when annotations are empty', async () => {
        const annotationToolContext = fakeAnnotationToolContext({
            annotations: [],
        });

        render(
            <ProjectProvider
                projectIdentifier={{
                    organizationId: 'organization-id',
                    workspaceId: 'workspace-id',
                    projectId: 'project-id',
                }}
            >
                <TaskProvider>
                    <AnnotationSceneProvider
                        annotations={annotationToolContext.scene.annotations}
                        labels={annotationToolContext.scene.labels}
                    >
                        <ZoomProvider>
                            <App annotationToolContext={annotationToolContext} />
                            <TransformComponent>{''}</TransformComponent>
                        </ZoomProvider>
                    </AnnotationSceneProvider>
                </TaskProvider>
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.getByTestId('annotation-all-annotations-toggle-visibility')).toBeDisabled();
    });

    describe('task chain aware', () => {
        it('bases its state on the output from the current task', async () => {
            const [firstLabel, ...otherLabels] = mockedLabels;
            const tasks = [
                getMockedTask({ id: '1', domain: DOMAIN.DETECTION, labels: [firstLabel] }),
                getMockedTask({ id: '2', domain: DOMAIN.SEGMENTATION, labels: otherLabels }),
            ];
            const annotationToolContext = fakeAnnotationToolContext({
                annotations: [
                    getMockedAnnotation({
                        id: '1',
                        isHidden: false,
                        labels: [labelFromUser(firstLabel)],
                        isSelected: true,
                    }),
                    getMockedAnnotation({ id: '2', isHidden: true, labels: [labelFromUser(otherLabels[0])] }),
                ],
                labels: mockedLabels,
            });

            jest.mocked(useTask).mockReturnValue(mockedTaskContextProps({ tasks, selectedTask: tasks[1] }));

            const { container } = render(
                <ProjectProvider
                    projectIdentifier={{
                        organizationId: 'organization-id',
                        workspaceId: 'workspace-id',
                        projectId: 'project-id',
                    }}
                >
                    <TaskProvider>
                        <AnnotationSceneProvider
                            annotations={annotationToolContext.scene.annotations}
                            labels={annotationToolContext.scene.labels}
                        >
                            <ZoomProvider>
                                <App annotationToolContext={annotationToolContext} />
                                <TransformComponent>{''}</TransformComponent>
                            </ZoomProvider>
                        </AnnotationSceneProvider>
                    </TaskProvider>
                </ProjectProvider>
            );

            await waitForElementToBeRemoved(screen.getByRole('progressbar'));

            const visibilityButton = getById(container, 'annotation-all-annotations-toggle-visibility');
            expect(visibilityButton).toBeInTheDocument();
            visibilityButton && fireEvent.click(visibilityButton);

            // Since the second task's annotations are all hidden the button should not
            // have a pressed state (i.e. it should show annotations when pressed)
            expect(visibilityButton).toHaveAttribute('aria-pressed', 'false');

            visibilityButton && fireEvent.click(visibilityButton);
            expect(visibilityButton).toHaveAttribute('aria-pressed', 'true');
        });
    });
});
