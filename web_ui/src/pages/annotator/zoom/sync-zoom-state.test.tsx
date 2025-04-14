// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { labelFromUser } from '../../../core/annotations/utils';
import { MEDIA_TYPE } from '../../../core/media/base-media.interface';
import { DOMAIN } from '../../../core/projects/core.interface';
import { getMockedAnnotation } from '../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImageMediaItem } from '../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedProject } from '../../../test-utils/mocked-items-factory/mocked-project';
import { useProject } from '../../project-details/providers/project-provider/project-provider.component';
import * as AnnotationScene from '../providers/annotation-scene-provider/annotation-scene-provider.component';
import { AnnotatorProvider } from '../providers/annotator-provider/annotator-provider.component';
import { DefaultSelectedMediaItemProvider } from '../providers/selected-media-item-provider/default-selected-media-item-provider.component';
import { SelectedMediaItem } from '../providers/selected-media-item-provider/selected-media-item.interface';
import { TaskProvider, useTask } from '../providers/task-provider/task-provider.component';
import { annotatorRender as render } from '../test-utils/annotator-render';
import { SyncZoomState, SyncZoomTarget } from './sync-zoom-state.component';
import { TransformZoomAnnotation } from './transform-zoom-annotation.component';
import { useZoom, ZoomProvider } from './zoom-provider.component';

jest.mock('./zoom-provider.component', () => ({
    ...jest.requireActual('./zoom-provider.component'),
    useZoom: jest.fn(),
}));

jest.mock('../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../providers/task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

jest.mock('../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(),
}));

describe('SyncZoomState', (): void => {
    beforeEach(() => {
        (useProject as jest.Mock).mockImplementation(() => ({
            project: getMockedProject({}),
            projectIdentifier,
            isSingleDomainProject: jest.fn(),
            domains: [],
        }));

        (useTask as jest.Mock).mockImplementation(() => ({
            tasks: [],
            selectedTask: null,
            activeDomains: [],
            labels: [],
            isTaskChainDomainSelected: () => false,
        }));

        // @ts-expect-error We only care about mocking the annotations
        jest.spyOn(AnnotationScene, 'useAnnotationScene').mockReturnValue({ annotations: [] });
    });

    afterEach(() => {
        jest.clearAllMocks();
        jest.resetModules();
    });

    const projectIdentifier = getMockedProjectIdentifier();
    const defaultSelectedMediaItem: SelectedMediaItem = {
        ...getMockedImageMediaItem({}),
        image: new ImageData(100, 100),
        annotations: [],
    };

    const otherSelectedMediaItem = {
        ...defaultSelectedMediaItem,
        ...getMockedImageMediaItem({
            name: 'yet another media image',
            identifier: { type: MEDIA_TYPE.IMAGE, imageId: 'test-image-2' },
        }),
    };

    const App = () => {
        const [selectedMediaItem2, setSelectedMediaItem] = useState(defaultSelectedMediaItem);
        const onClick = () => {
            // Trigger changing an image so that we can verify that the zoom is reset
            setSelectedMediaItem(otherSelectedMediaItem);
        };

        return (
            <ZoomProvider>
                <TaskProvider>
                    <DefaultSelectedMediaItemProvider selectedMediaItem={selectedMediaItem2}>
                        <button onClick={onClick}>Change image</button>
                        <SyncZoomState />
                        <SyncZoomTarget />
                        <AnnotatorProvider>
                            <TransformZoomAnnotation />
                        </AnnotatorProvider>
                    </DefaultSelectedMediaItemProvider>
                </TaskProvider>
            </ZoomProvider>
        );
    };

    it('sets the zoom target fitted to the screen upon mount', async () => {
        const mockSetZoomTargetOnRoi = jest.fn();

        (useZoom as jest.Mock).mockImplementation(() => ({
            setZoomTarget: jest.fn(),
            setZoomTargetOnRoi: mockSetZoomTargetOnRoi,
            getZoomStateForTarget: jest.fn(() => ({ zoom: 1.0, translation: { x: 0, y: 0 } })),
            setZoomState: jest.fn(),
            setScreenSize: jest.fn(),
            zoomState: { zoom: {} },
        }));

        await render(<App />);

        await waitFor(() => {
            expect(mockSetZoomTargetOnRoi).toHaveBeenCalledWith({
                x: 0,
                y: 0,
                width: defaultSelectedMediaItem.image.width,
                height: defaultSelectedMediaItem.image.height,
            });
        });
    });

    it('resets the zoomState if the image changes', async () => {
        const mockSetZoomTargetOnRoi = jest.fn();
        (useZoom as jest.Mock).mockImplementation(() => ({
            setZoomTarget: jest.fn(),
            setZoomTargetOnRoi: mockSetZoomTargetOnRoi,
            getZoomStateForTarget: jest.fn(() => ({ zoom: 1.0, translation: { x: 0, y: 0 } })),
            setZoomState: jest.fn(),
            setScreenSize: jest.fn(),
            screenSize: undefined,
            zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } },
        }));

        await render(<App />);

        await waitFor(() => {
            expect(mockSetZoomTargetOnRoi).toHaveBeenCalledWith({
                x: 0,
                y: 0,
                width: defaultSelectedMediaItem.image.width,
                height: defaultSelectedMediaItem.image.height,
            });
        });

        fireEvent.click(screen.getByRole('button', { name: 'Change image' }));

        await waitFor(() => {
            expect(mockSetZoomTargetOnRoi).toHaveBeenLastCalledWith(
                expect.objectContaining({
                    x: 0,
                    y: 0,
                    width: otherSelectedMediaItem.image.width,
                    height: otherSelectedMediaItem.image.height,
                })
            );
        });
    });

    it('zooms into the annotation if the task is local', async () => {
        const mockSetZoomTarget = jest.fn();
        const fakeLabelOne = getMockedLabel({ id: 'fake-label-1' });
        const fakeLabelTwo = getMockedLabel({ id: 'fake-label-2' });
        const fakeAnnotation = getMockedAnnotation({
            id: 'fake-annotation',
            isSelected: true,
            labels: [labelFromUser(fakeLabelOne), labelFromUser(fakeLabelTwo)],
        });
        const fakeTasks = [
            { id: 'test-task-1', title: 'test-1', labels: [fakeLabelOne], domain: DOMAIN.DETECTION },
            { id: 'test-task-2', title: 'test-2', labels: [fakeLabelTwo], domain: DOMAIN.SEGMENTATION },
        ];

        // @ts-expect-error We only care about mocking the annotations
        jest.spyOn(AnnotationScene, 'useAnnotationScene').mockReturnValue({ annotations: [fakeAnnotation] });

        (useZoom as jest.Mock).mockImplementation(() => ({
            setZoomTarget: mockSetZoomTarget,
            setZoomTargetOnRoi: jest.fn(),
            getZoomStateForTarget: jest.fn(() => ({ zoom: 1.0, translation: { x: 0, y: 0 } })),
            setZoomState: jest.fn(),
            setScreenSize: jest.fn(),
            zoomState: { zoom: {} },
        }));

        (useTask as jest.Mock).mockImplementation(() => ({
            tasks: fakeTasks,
            selectedTask: fakeTasks[1],
            activeDomains: [fakeTasks[1].domain],
            labels: fakeTasks[1].labels,
            isTaskChainDomainSelected: () => false,
        }));

        (useProject as jest.Mock).mockImplementation(() => ({
            project: getMockedProject({
                tasks: fakeTasks,
            }),
            projectIdentifier,
            isSingleDomainProject: jest.fn(),
            domains: [],
        }));

        await render(<App />);

        await waitFor(() => {
            expect(mockSetZoomTarget).toHaveBeenLastCalledWith(expect.any(Function));
        });
    });

    it('resets zoom if it was zoomed into an annotation and the user changes images', async () => {
        const mockSetZoomTarget = jest.fn();
        const mockSetZoomTargetOnRoi = jest.fn();
        const fakeLabelOne = getMockedLabel({ id: 'fake-label-1' });
        const fakeLabelTwo = getMockedLabel({ id: 'fake-label-2' });
        const fakeAnnotation = getMockedAnnotation({
            id: 'fake-annotation',
            isSelected: true,
            labels: [labelFromUser(fakeLabelOne), labelFromUser(fakeLabelTwo)],
        });
        const fakeTasks = [
            { id: 'test-task-1', title: 'test-1', labels: [fakeLabelOne], domain: DOMAIN.DETECTION },
            { id: 'test-task-2', title: 'test-2', labels: [fakeLabelTwo], domain: DOMAIN.SEGMENTATION },
        ];

        // @ts-expect-error We only care about mocking the annotations
        jest.spyOn(AnnotationScene, 'useAnnotationScene').mockReturnValue({ annotations: [fakeAnnotation] });

        (useZoom as jest.Mock).mockImplementation(() => ({
            setZoomTarget: mockSetZoomTarget,
            setZoomTargetOnRoi: mockSetZoomTargetOnRoi,
            getZoomStateForTarget: jest.fn(() => ({ zoom: 1.0, translation: { x: 0, y: 0 } })),
            setZoomState: jest.fn(),
            setScreenSize: jest.fn(),
            zoomState: { zoom: {} },
        }));

        (useTask as jest.Mock).mockImplementation(() => ({
            tasks: fakeTasks,
            labels: fakeTasks[1].labels,
            selectedTask: fakeTasks[1],
            activeDomains: [fakeTasks[1].domain],
            isTaskChainDomainSelected: () => false,
        }));

        (useProject as jest.Mock).mockImplementation(() => ({
            project: getMockedProject({
                tasks: fakeTasks,
            }),
            projectIdentifier,
            isSingleDomainProject: jest.fn(),
            domains: [],
        }));

        await render(<App />);

        await waitFor(() => {
            expect(mockSetZoomTarget).toHaveBeenLastCalledWith(expect.any(Function));
        });

        fireEvent.click(screen.getByRole('button', { name: 'Change image' }));

        await waitFor(() => {
            expect(mockSetZoomTargetOnRoi).toHaveBeenLastCalledWith(
                expect.objectContaining({
                    x: 0,
                    y: 0,
                    width: otherSelectedMediaItem.image.width,
                    height: otherSelectedMediaItem.image.height,
                })
            );
        });
    });
});
