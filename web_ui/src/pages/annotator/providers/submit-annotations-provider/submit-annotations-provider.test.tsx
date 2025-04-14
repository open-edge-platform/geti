// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { act, fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';
import { v4 as uuidv4 } from 'uuid';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedUserProjectSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { renderHookWithProviders } from '../../../../test-utils/render-hook-with-providers';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { getMockedImage } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { AnalyticsAnnotationSceneProvider } from '../analytics-annotation-scene-provider/analytics-annotation-scene-provider.component';
import { AnnotationSceneProvider } from '../annotation-scene-provider/annotation-scene-provider.component';
import { AnnotationThresholdProvider } from '../annotation-threshold-provider/annotation-threshold-provider.component';
import { useAnnotator } from '../annotator-provider/annotator-provider.component';
import { PredictionProvider } from '../prediction-provider/prediction-provider.component';
import {
    SelectedMediaItemProps,
    useSelectedMediaItem,
} from '../selected-media-item-provider/selected-media-item-provider.component';
import { SelectedMediaItem } from '../selected-media-item-provider/selected-media-item.interface';
import { TaskChainProvider } from '../task-chain-provider/task-chain-provider.component';
import { useTask } from '../task-provider/task-provider.component';
import { SubmitAnnotationsProvider, useSubmitAnnotations } from './submit-annotations-provider.component';

jest.mock('../selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(() => ({
        selectedMediaItemQuery: { isLoading: false },
    })),
}));

jest.mock('../task-provider/task-provider.component', () => ({
    ...jest.requireActual('../task-provider/task-provider.component'),
    useTask: jest.fn(() => ({})),
}));

jest.mock('../annotator-provider/annotator-provider.component', () => ({
    useAnnotator: jest.fn(),
}));

jest.mock('uuid', () => ({
    ...jest.requireActual('uuid'),
    v4: jest.fn(),
}));

// @ts-expect-error we're only interested in mocking the selected task
jest.mocked(useTask).mockImplementation(() => {
    const selectedTask = getMockedTask({ domain: DOMAIN.SEGMENTATION });
    return { selectedTask, tasks: [selectedTask], isTaskChainDomainSelected: () => false };
});

describe('Saving annotations', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const selectedMediaItem: SelectedMediaItem = {
        ...getMockedImageMediaItem({}),
        image: getMockedImage(),
        annotations: [],
    };

    const render = async (app: JSX.Element, annotations: Annotation[], withoutSelectedMediaItem = false) => {
        const setSelectedMediaItem = jest.fn();
        const saveAnnotations = jest.fn();
        const discardAnnotations = jest.fn();
        const { scene } = fakeAnnotationToolContext({ annotations });

        providersRender(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <AnnotationSceneProvider annotations={annotations} labels={[]}>
                    <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                        <AnalyticsAnnotationSceneProvider activeTool={ToolType.BoxTool}>
                            <TaskChainProvider tasks={[]} selectedTask={null} defaultLabel={null}>
                                <PredictionProvider
                                    settings={getMockedUserProjectSettingsObject()}
                                    explanations={[]}
                                    initPredictions={[]}
                                    userAnnotationScene={scene}
                                >
                                    <SubmitAnnotationsProvider
                                        settings={getMockedUserProjectSettingsObject()}
                                        annotations={annotations}
                                        saveAnnotations={saveAnnotations}
                                        discardAnnotations={discardAnnotations}
                                        currentMediaItem={withoutSelectedMediaItem ? undefined : selectedMediaItem}
                                    >
                                        {app}
                                    </SubmitAnnotationsProvider>
                                </PredictionProvider>
                            </TaskChainProvider>
                        </AnalyticsAnnotationSceneProvider>
                    </AnnotationThresholdProvider>
                </AnnotationSceneProvider>
            </ProjectProvider>
        );
        await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));

        return { setSelectedMediaItem, saveAnnotations, discardAnnotations };
    };

    describe('Submitting annotations', () => {
        const App = ({ callback, annotations }: { callback?: () => Promise<void>; annotations: Annotation[] }) => {
            const { submitAnnotationsMutation } = useSubmitAnnotations();
            const isSaving = submitAnnotationsMutation.isPending;

            return (
                <button onClick={() => submitAnnotationsMutation.mutate({ callback, annotations })} disabled={isSaving}>
                    {isSaving ? 'Loading' : 'Submit'}
                </button>
            );
        };

        const annotations: Annotation[] = [{ ...getMockedAnnotation({}), labels: [labelFromUser(getMockedLabel())] }];

        it('Saves annotations then calls a callback', async () => {
            const callback = jest.fn();
            const { saveAnnotations } = await render(
                <App callback={callback} annotations={annotations} />,
                annotations
            );

            fireEvent.click(screen.getByRole('button'));

            await waitFor(() => {
                expect(screen.queryByRole('button', { name: /loading/i })).not.toBeInTheDocument();
            });

            expect(callback).toHaveBeenCalled();
            expect(saveAnnotations).toHaveBeenCalledWith(annotations);
        });

        it('Only calls a callback when there are no changes', async () => {
            const callback = jest.fn();
            const { saveAnnotations } = await render(
                <App callback={callback} annotations={selectedMediaItem.annotations} />,
                selectedMediaItem.annotations
            );

            fireEvent.click(screen.getByRole('button'));

            await waitFor(() => {
                expect(screen.queryByRole('button', { name: /loading/i })).not.toBeInTheDocument();
            });

            expect(callback).toHaveBeenCalled();
            expect(saveAnnotations).not.toHaveBeenCalled();
        });

        it('Shows an error dialog when saving fails', async () => {
            const callback = jest.fn();
            const { saveAnnotations } = await render(
                <App callback={callback} annotations={annotations} />,
                annotations
            );

            const errorMessage = 'A server error occured';
            saveAnnotations.mockImplementation(() => {
                throw new Error(errorMessage);
            });

            fireEvent.click(screen.getByRole('button'));

            await waitFor(() => {
                expect(screen.queryByRole('button', { name: /loading/i })).not.toBeInTheDocument();
            });

            expect(callback).not.toHaveBeenCalled();
            expect(saveAnnotations).toHaveBeenCalledWith(annotations);
            expect(saveAnnotations).toThrow(new Error(errorMessage));

            expect(screen.getByText(errorMessage)).toBeInTheDocument();
        });

        it('Submits unfinished annotations', async () => {
            const SetUnfinishedAnnotations = ({ unfinishedAnnotations }: { unfinishedAnnotations: Annotation[] }) => {
                const { setUnfinishedShapeCallback } = useSubmitAnnotations();
                const handleClick = () => {
                    setUnfinishedShapeCallback(() => unfinishedAnnotations);
                };

                return <button onClick={handleClick}>Set unfinished annotations</button>;
            };

            const callback = jest.fn();
            const { saveAnnotations } = await render(
                <>
                    <App callback={callback} annotations={annotations} />
                    <SetUnfinishedAnnotations unfinishedAnnotations={annotations} />
                </>,
                []
            );

            fireEvent.click(screen.getByRole('button', { name: /Set unfinished annotations/i }));
            fireEvent.click(screen.getByRole('button', { name: /Submit/i }));

            await waitFor(() => {
                expect(screen.queryByRole('button', { name: /loading/i })).not.toBeInTheDocument();
            });

            expect(callback).toHaveBeenCalled();
            expect(saveAnnotations).toHaveBeenCalledWith(annotations);
        });

        describe('Handling invalid user annotation scene', () => {
            const invalidAnnotations = [
                { ...getMockedAnnotation({ id: 'test-1' }), labels: [labelFromUser(getMockedLabel())] },
                { ...getMockedAnnotation({ id: 'test-2' }), labels: [] },
            ];

            it('Shows a dialog informing the user of invalid annotations', async () => {
                const callback = jest.fn();
                const { saveAnnotations } = await render(
                    <App callback={callback} annotations={invalidAnnotations} />,
                    invalidAnnotations
                );

                fireEvent.click(screen.getByRole('button'));

                expect(await screen.findByRole('alertdialog')).toBeInTheDocument();

                expect(callback).not.toHaveBeenCalled();
                expect(saveAnnotations).not.toHaveBeenCalledWith(annotations);

                fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));

                expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();

                expect(callback).not.toHaveBeenCalled();
                expect(saveAnnotations).not.toHaveBeenCalledWith(invalidAnnotations);
            });

            it('Shows a dialog informing the user of invalid annotations and removes invalid annotations', async () => {
                const callback = jest.fn();
                const { saveAnnotations } = await render(
                    <App callback={callback} annotations={invalidAnnotations} />,
                    invalidAnnotations
                );

                fireEvent.click(screen.getByRole('button'));

                expect(await screen.findByRole('alertdialog')).toBeInTheDocument();

                expect(callback).not.toHaveBeenCalled();
                expect(saveAnnotations).not.toHaveBeenCalledWith(annotations);

                fireEvent.click(screen.getByRole('button', { name: /Delete & continue/i }));

                await waitForElementToBeRemoved(screen.getByRole('alertdialog'));

                expect(callback).toHaveBeenCalled();
                expect(saveAnnotations).toHaveBeenCalledWith([invalidAnnotations[0]]);
            });
        });

        describe('Adding empty labels when submitting an empty annotation scene', () => {
            it.todo('Classification');
            it.todo('Detection');
            it.todo('Segmentation');
            describe('Task chain', () => {
                it.todo('Detection -> Classification');
                it.todo('Detection -> Segmentation');
            });
        });
    });

    describe('Asking user for confirmation to submit or discard', () => {
        const App = ({ callback }: { callback?: () => Promise<void> }) => {
            const { confirmSaveAnnotations } = useSubmitAnnotations();

            return <button onClick={() => confirmSaveAnnotations(callback)}>Show confirmation</button>;
        };

        const annotations: Annotation[] = [{ ...getMockedAnnotation({}), labels: [labelFromUser(getMockedLabel())] }];

        it('Discards changes then calls a callback', async () => {
            const callback = jest.fn();
            const { saveAnnotations, discardAnnotations } = await render(<App callback={callback} />, annotations);

            fireEvent.click(screen.getByRole('button'));

            expect(screen.getByRole('dialog')).toBeInTheDocument();

            fireEvent.click(screen.getByRole('button', { name: /Discard/i }));

            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
            expect(callback).toHaveBeenCalled();
            expect(saveAnnotations).not.toHaveBeenCalled();
            expect(discardAnnotations).toHaveBeenCalled();
        });

        it('Saves annotations then calls a callback', async () => {
            const callback = jest.fn();
            const { saveAnnotations } = await render(<App callback={callback} />, annotations);

            fireEvent.click(screen.getByRole('button'));

            expect(screen.getByRole('dialog')).toBeInTheDocument();

            fireEvent.click(screen.getByRole('button', { name: /Submit/i }));

            await waitFor(() => {
                expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
            });

            expect(callback).toHaveBeenCalled();
            expect(saveAnnotations).toHaveBeenCalledWith(annotations);
        });

        it('Shows an error message when saving fails', async () => {
            const callback = jest.fn();
            const { saveAnnotations } = await render(<App callback={callback} />, annotations);

            const errorMessage = 'A server error occured';
            saveAnnotations.mockImplementation(() => {
                throw new Error(errorMessage);
            });

            fireEvent.click(screen.getByRole('button'));

            expect(screen.getByRole('dialog')).toBeInTheDocument();

            fireEvent.click(screen.getByRole('button', { name: /Submit/i }));

            await waitFor(() => {
                expect(saveAnnotations).toHaveBeenCalledWith(annotations);
            });

            expect(screen.queryByRole('dialog')).toBeInTheDocument();
            expect(screen.getByText(errorMessage)).toBeInTheDocument();
            expect(callback).not.toHaveBeenCalled();
            expect(saveAnnotations).toThrow(new Error(errorMessage));
        });

        it('Cancels the confirmation and does not call a callback', async () => {
            const callback = jest.fn();
            const { saveAnnotations } = await render(<App callback={callback} />, annotations);

            fireEvent.click(screen.getByRole('button'));

            expect(screen.getByRole('dialog')).toBeInTheDocument();

            fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));

            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
            expect(callback).not.toHaveBeenCalled();
            expect(saveAnnotations).not.toHaveBeenCalled();
        });

        it("Doesn't show a confirmation dialog if there are no changes", async () => {
            const callback = jest.fn();
            const { saveAnnotations } = await render(<App callback={callback} />, selectedMediaItem.annotations);

            fireEvent.click(screen.getByRole('button'));

            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
            expect(callback).toHaveBeenCalled();
            expect(saveAnnotations).not.toHaveBeenCalled();
        });

        it('Does not allow to submit while loading media', async () => {
            // @ts-expect-error This is a bad mock
            jest.mocked(useSelectedMediaItem).mockImplementation(() => ({
                selectedMediaItemQuery: { isPending: true },
            }));

            const callback = jest.fn();
            await render(<App callback={callback} />, annotations);

            fireEvent.click(screen.getByRole('button'));

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /Submit/i })).toBeDisabled();
        });
    });

    it('Requires the SubmitAnnotationsProvider', () => {
        // Expect an error to be thrown when rendering app
        const App = () => {
            useSubmitAnnotations();

            return null;
        };

        const spy = jest.spyOn(console, 'error').mockImplementation();
        expect(() => providersRender(<App />)).toThrow();
        expect(spy).toHaveBeenCalledTimes(3);

        spy.mockRestore();
    });
});

describe('useSubmitAnnotations', () => {
    const wrapper = ({
        children,
        annotations,
        selectedTask,
        saveAnnotations,
        selectedMediaItem,
    }: {
        children?: ReactNode;
        selectedTask: Task;
        annotations: Annotation[];
        saveAnnotations: (annotations: ReadonlyArray<Annotation>) => Promise<void>;
        selectedMediaItem: SelectedMediaItem;
    }) => {
        // @ts-expect-error we're only interested in mocking the selected task
        jest.mocked(useTask).mockImplementation(() => {
            return { selectedTask, tasks: [selectedTask], isTaskChainDomainSelected: () => false };
        });

        jest.mocked(useSelectedMediaItem).mockImplementation(
            () => ({ selectedMediaItem }) as unknown as SelectedMediaItemProps
        );

        // @ts-expect-error We only care about mocking the selected media item query
        jest.mocked(useAnnotator).mockImplementation(() => {
            return { selectedMediaItem, isPredictionRejected: jest.fn(() => false) };
        });
        const { scene } = fakeAnnotationToolContext({ annotations });

        return (
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <AnnotationSceneProvider annotations={annotations} labels={[]}>
                    <AnalyticsAnnotationSceneProvider activeTool={ToolType.BoxTool}>
                        <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                            <TaskChainProvider tasks={[]} selectedTask={null} defaultLabel={null}>
                                <PredictionProvider
                                    explanations={[]}
                                    initPredictions={[]}
                                    userAnnotationScene={scene}
                                    settings={getMockedUserProjectSettingsObject()}
                                >
                                    <SubmitAnnotationsProvider
                                        settings={getMockedUserProjectSettingsObject()}
                                        annotations={annotations}
                                        discardAnnotations={jest.fn()}
                                        saveAnnotations={saveAnnotations}
                                        currentMediaItem={selectedMediaItem}
                                    >
                                        {children}
                                    </SubmitAnnotationsProvider>
                                </PredictionProvider>
                            </TaskChainProvider>
                        </AnnotationThresholdProvider>
                    </AnalyticsAnnotationSceneProvider>
                </AnnotationSceneProvider>
            </ProjectProvider>
        );
    };

    const renderSubmitAnnotationsHook = ({
        saveAnnotations,
        selectedMediaItem,
        annotations,
        selectedTask,
    }: {
        selectedTask: Task;
        annotations: Annotation[];
        saveAnnotations: (annotations: ReadonlyArray<Annotation>) => Promise<void>;
        selectedMediaItem: SelectedMediaItem;
    }) => {
        return renderHookWithProviders(useSubmitAnnotations, {
            wrapper: ({ children }) =>
                wrapper({ children, selectedTask, annotations, saveAnnotations, selectedMediaItem }),
        });
    };

    describe('Classification', () => {
        it('submits empty annotations when saving a global annotation without labels', async () => {
            const selectedTask = getMockedTask({ domain: DOMAIN.CLASSIFICATION });
            const imageROI = { x: 0, y: 0, width: 100, height: 100 };
            const annotations = [
                getMockedAnnotation({ labels: [], shape: { shapeType: ShapeType.Rect, ...imageROI } }),
            ];

            const selectedMediaItem: SelectedMediaItem = {
                ...getMockedImageMediaItem({}),
                image: { ...getMockedImage(), ...imageROI },
                annotations: [
                    getMockedAnnotation({
                        labels: [labelFromUser(getMockedLabel())],
                        shape: { shapeType: ShapeType.Rect, ...imageROI },
                    }),
                ],
            };

            const saveAnnotations = jest.fn();

            const { result } = renderSubmitAnnotationsHook({
                selectedTask,
                annotations,
                saveAnnotations,
                selectedMediaItem,
            });

            await waitFor(() => {
                expect(result.current).toBeDefined();
            });

            act(() => {
                result.current.submitAnnotationsMutation.mutate({
                    annotations,
                    callback: jest.fn(),
                });
            });

            await waitFor(() => {
                expect(saveAnnotations).toHaveBeenCalledWith([]);
            });
        });
    });

    describe('Anomaly tasks', () => {
        const normalLabel = getMockedLabel({
            id: 'normal-label-id',
            name: 'Normal',
            behaviour: LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.GLOBAL,
        });

        const anomalousLabel = getMockedLabel({
            id: 'anomalous-label-id',
            name: 'Anomalous',
            behaviour: LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.ANOMALOUS,
        });

        const selectedTask = getMockedTask({
            id: 'anomaly-segmentation',
            domain: DOMAIN.ANOMALY_SEGMENTATION,
            labels: [normalLabel, anomalousLabel],
        });

        const imageROI = { x: 0, y: 0, width: 100, height: 100 };
        const globalAnomalousAnnotation = getMockedAnnotation({
            labels: [labelFromUser(anomalousLabel)],
            shape: { shapeType: ShapeType.Rect, ...imageROI },
        });

        it('Submits empty annotations when saving a global annotation without labels and no local annotations', async () => {
            const annotations = [getMockedAnnotation({ ...globalAnomalousAnnotation, labels: [] })];

            const selectedMediaItem: SelectedMediaItem = {
                ...getMockedImageMediaItem({}),
                image: { ...getMockedImage(), ...imageROI },
                annotations: [
                    getMockedAnnotation({
                        labels: [labelFromUser(getMockedLabel())],
                        shape: { shapeType: ShapeType.Rect, ...imageROI },
                    }),
                ],
            };

            const saveAnnotations = jest.fn();

            const { result } = renderSubmitAnnotationsHook({
                selectedTask,
                annotations,
                saveAnnotations,
                selectedMediaItem,
            });

            await waitFor(() => {
                expect(result.current).toBeDefined();
            });

            act(() => {
                result.current.submitAnnotationsMutation.mutate({
                    annotations,
                    callback: jest.fn(),
                });
            });

            await waitFor(() => {
                expect(saveAnnotations).toHaveBeenCalledWith([]);
            });
        });

        it('Does not add a second global anomalous annotation when saving', async () => {
            const annotations = [
                globalAnomalousAnnotation,
                getMockedAnnotation({
                    id: 'local-anomalous',
                    labels: [labelFromUser(anomalousLabel)],
                    shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                }),
            ];

            const selectedMediaItem: SelectedMediaItem = {
                ...getMockedImageMediaItem({}),
                image: { ...getMockedImage(), ...imageROI },
                annotations: [],
            };

            const saveAnnotations = jest.fn();
            const { result } = renderSubmitAnnotationsHook({
                selectedTask,
                annotations,
                saveAnnotations,
                selectedMediaItem,
            });

            await waitFor(() => {
                expect(result.current).toBeDefined();
            });

            act(() => {
                result.current.submitAnnotationsMutation.mutate({
                    annotations,
                    callback: jest.fn(),
                });
            });

            await waitFor(() => {
                expect(saveAnnotations).toHaveBeenCalledWith(annotations);
            });
        });

        it('Adds a global annotation when only saving local anomalous annotations', async () => {
            const globalId = 'global-annotation-id';
            jest.mocked<() => string>(uuidv4).mockImplementation(() => globalId);

            const annotations = [
                getMockedAnnotation({
                    id: 'local-anomalous',
                    labels: [labelFromUser(anomalousLabel)],
                    shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                }),
            ];

            const selectedMediaItem: SelectedMediaItem = {
                ...getMockedImageMediaItem({}),
                image: { ...getMockedImage(), ...imageROI },
                annotations: [],
            };

            const saveAnnotations = jest.fn();

            const { result } = renderSubmitAnnotationsHook({
                selectedTask,
                annotations,
                saveAnnotations,
                selectedMediaItem,
            });

            await waitFor(() => {
                expect(result.current).toBeDefined();
            });

            const callback = jest.fn();
            act(() => {
                result.current.submitAnnotationsMutation.mutate({
                    annotations,
                    callback,
                });
            });

            await waitFor(() => {
                expect(saveAnnotations).toHaveBeenCalledWith([
                    { ...globalAnomalousAnnotation, id: globalId, zIndex: 1 },
                    ...annotations,
                ]);
            });
        });

        it('Adds a anomalous label when saving local anomalous annotations and a global annotation without labels', async () => {
            const globalId = 'global-annotation-id';
            jest.mocked<() => string>(uuidv4).mockImplementation(() => globalId);

            const annotations = [
                { ...globalAnomalousAnnotation, labels: [] },
                getMockedAnnotation({
                    id: 'local-anomalous',
                    labels: [labelFromUser(anomalousLabel)],
                    shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                }),
            ];

            const selectedMediaItem: SelectedMediaItem = {
                ...getMockedImageMediaItem({}),
                image: { ...getMockedImage(), ...imageROI },
                annotations: [],
            };

            const saveAnnotations = jest.fn();
            const { result } = renderSubmitAnnotationsHook({
                selectedTask,
                annotations,
                saveAnnotations,
                selectedMediaItem,
            });

            await waitFor(() => {
                expect(result.current).toBeDefined();
            });

            act(() => {
                result.current.submitAnnotationsMutation.mutate({
                    annotations,
                    callback: jest.fn(),
                });
            });

            await waitFor(() => {
                expect(saveAnnotations).toHaveBeenCalledWith([globalAnomalousAnnotation, annotations[1]]);
            });
        });
    });
});
