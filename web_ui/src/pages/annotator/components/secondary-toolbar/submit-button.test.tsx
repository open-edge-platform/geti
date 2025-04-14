// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { useMutation } from '@tanstack/react-query';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { labelFromModel, labelFromUser } from '../../../../core/annotations/utils';
import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { AnnotationStatePerTask, MEDIA_ANNOTATION_STATUS } from '../../../../core/media/base.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { createInMemoryMediaService } from '../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import {
    getMockedImageMediaItem,
    getMockedVideoFrameMediaItem,
} from '../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { AnnotationThresholdProvider } from '../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { useAnnotator } from '../../providers/annotator-provider/annotator-provider.component';
import { DefaultHotkeys } from '../../providers/annotator-provider/utils';
import { DatasetProvider } from '../../providers/dataset-provider/dataset-provider.component';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import {
    SubmitAnnotationsContextProps,
    useSubmitAnnotations,
} from '../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { SaveAnnotationMutation } from '../../providers/submit-annotations-provider/submit-annotations.interface';
import { useTaskChainOutput } from '../../providers/task-chain-provider/use-task-chain-output.hook';
import { useVideoPlayerContext } from '../video-player/video-player-provider.component';
import { SubmitButton } from './submit-button.component';

const getMockedMediaItem = (
    index = 0,
    state: AnnotationStatePerTask[] = [
        {
            taskId: `image-id-${index}`,
            state: MEDIA_ANNOTATION_STATUS.NONE,
        },
    ]
): MediaItem => {
    return getMockedImageMediaItem({
        identifier: { type: MEDIA_TYPE.IMAGE, imageId: `${index}` },
        annotationStatePerTask: state,
    });
};

jest.mock('../../providers/submit-annotations-provider/submit-annotations-provider.component', () => ({
    ...jest.requireActual('../../providers/submit-annotations-provider/submit-annotations-provider.component'),
    useSubmitAnnotations: jest.fn(),
}));

jest.mock('../../providers/selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../../providers/selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(() => ({ selectedMediaItemQuery: { isPending: false } })),
}));

jest.mock('../video-player/video-player-provider.component', () => ({
    useVideoPlayerContext: jest.fn(() => undefined),
}));

jest.mock('../../../project-details/providers/project-provider/project-provider.component', () => ({
    useProject: jest.fn(() => ({
        isSingleDomainProject: () => false,
        project: { datasets: ['dataset-id'] },
    })),
}));

jest.mock('../../providers/task-chain-provider/task-chain-provider.component', () => ({
    useTaskChain: jest.fn(() => ({
        inputs: [],
    })),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    useTask: jest.fn(() => ({
        selectedTask: null,
    })),
}));

jest.mock('../../providers/annotator-provider/annotator-provider.component', () => ({
    useAnnotator: jest.fn(() => ({
        hotKeys: {},
    })),
}));

jest.mock('../../providers/task-chain-provider/use-task-chain-output.hook', () => ({
    useTaskChainOutput: jest.fn(() => []),
}));

jest.mock('../video-player/video-player-provider.component');

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
        projectId: 'project-id',
    }),
}));

const prediction = getMockedAnnotation({
    labels: [labelFromModel(getMockedLabel({}), 0.5, '123', '321')],
});
const userAnnotations = getMockedAnnotation({
    labels: [labelFromUser(getMockedLabel({}))],
});

describe('Submit annotations button', () => {
    const items = [getMockedMediaItem(0), getMockedMediaItem(1), getMockedMediaItem(2), getMockedMediaItem(3)];

    const App = ({
        mediaItem,
        selectMediaItem,
        canSubmit,
        submitMutation,
        annotations = [],
        newAnnotations = [],
    }: {
        mediaItem: MediaItem;
        selectMediaItem: (mediaItem: MediaItem) => void;
        submitMutation: (arg: SaveAnnotationMutation) => Promise<void>;
        canSubmit: boolean;
        annotations?: Annotation[];
        newAnnotations: Annotation[];
    }) => {
        const [selectedMediaItem, setSelectedMediaItem] = useState(mediaItem);
        const mutation = useMutation({
            mutationFn: async (arg: SaveAnnotationMutation) => {
                await submitMutation(arg);

                if (arg.callback) {
                    await arg.callback();
                }
            },
        });
        const mockAnnotationToolContext = fakeAnnotationToolContext({ annotations });

        jest.mocked(useSubmitAnnotations).mockReturnValue({
            submitAnnotationsMutation: mutation,
        } as SubmitAnnotationsContextProps);

        return (
            <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                <DatasetProvider>
                    <SubmitButton
                        canSubmit={canSubmit}
                        newAnnotations={newAnnotations}
                        selectMediaItem={(newMediaItem) => {
                            setSelectedMediaItem(newMediaItem);
                            selectMediaItem(newMediaItem);
                        }}
                        selectedMediaItem={selectedMediaItem}
                        annotationToolContext={mockAnnotationToolContext}
                    />
                </DatasetProvider>
            </AnnotationThresholdProvider>
        );
    };

    beforeEach(() => {
        (useAnnotator as jest.Mock).mockImplementation(() => {
            return {
                mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
                hotKeys: DefaultHotkeys,
            };
        });
        jest.mocked(useTaskChainOutput).mockImplementation(() => []);
        jest.mocked(useVideoPlayerContext).mockImplementation(() => undefined);
    });

    it('Submits annotations and stays if there are no unannotated media', async () => {
        const mediaItem = getMockedMediaItem(123, [{ taskId: 'fake-id', state: MEDIA_ANNOTATION_STATUS.NONE }]);
        const newAnnotations: Annotation[] = [];
        const selectMediaItem = jest.fn();
        const submit = { mutate: jest.fn() };
        const mediaService = createInMemoryMediaService([mediaItem]);

        render(
            <App
                mediaItem={mediaItem}
                selectMediaItem={selectMediaItem}
                submitMutation={submit.mutate}
                newAnnotations={newAnnotations}
                canSubmit
            />,
            {
                services: {
                    mediaService,
                },
            }
        );

        const btn = screen.getByRole('button', { name: /submit annotations/i });
        expect(btn).toHaveTextContent('Submit');
        expect(btn).toBeEnabled();

        fireEvent.click(btn);

        await waitFor(() => {
            expect(submit.mutate).toHaveBeenCalledWith({
                annotations: newAnnotations,
                callback: expect.anything(),
            });
            expect(selectMediaItem).toHaveBeenCalledWith(mediaItem);
        });
    });

    it('Is disabled if there are no unannotated media and the user has made no changes', async () => {
        const mediaItem = items[1];
        const selectMediaItem = jest.fn();
        const submit = {
            mutate: jest.fn(),
        };
        const mediaService = createInMemoryMediaService([mediaItem]);

        render(
            <App
                mediaItem={mediaItem}
                selectMediaItem={selectMediaItem}
                submitMutation={submit.mutate}
                canSubmit={false}
                newAnnotations={[]}
            />,
            {
                services: {
                    mediaService,
                },
            }
        );

        const btn = screen.getByRole('button', { name: /submit annotations/i });
        expect(btn).toHaveTextContent('Submit');
        expect(btn).toBeDisabled();
    });

    it('Submits annotations and selects the next unannotated media item from the dataset', async () => {
        const mediaItem = items[1];
        const mediaService = createInMemoryMediaService(items);
        const selectMediaItem = jest.fn();
        const submit = {
            mutate: jest.fn(),
        };

        render(
            <App
                mediaItem={mediaItem}
                selectMediaItem={selectMediaItem}
                submitMutation={submit.mutate}
                newAnnotations={[]}
                canSubmit
            />,
            {
                services: {
                    mediaService,
                },
            }
        );

        const btn = await screen.findByRole('button', { name: /submit annotations/i });

        await waitFor(async () => {
            expect(btn).toHaveTextContent('Submit »');
            expect(btn).toBeEnabled();
        });

        fireEvent.click(btn);

        await waitFor(() => {
            expect(selectMediaItem).toHaveBeenCalledWith(items[2]);
            expect(submit.mutate).toHaveBeenCalled();
        });
    });

    it('Selects the next unannotated media item from the dataset when there are no changed annotations', async () => {
        const mediaItem = items[1];
        const mediaService = createInMemoryMediaService(items);

        const selectMediaItem = jest.fn();
        const submit = {
            mutate: jest.fn(),
        };

        render(
            <App
                mediaItem={mediaItem}
                selectMediaItem={selectMediaItem}
                submitMutation={submit.mutate}
                canSubmit={false}
                newAnnotations={[]}
            />,
            {
                services: {
                    mediaService,
                },
            }
        );

        const btn = await screen.findByRole('button', { name: /submit annotations/i });

        await waitFor(async () => {
            expect(btn).toHaveTextContent('Submit »');
            expect(btn).toBeEnabled();
        });

        fireEvent.click(btn);

        await waitFor(() => {
            expect(selectMediaItem).toHaveBeenCalledWith(items[2]);
        });
    });

    it('Selects the next media item from the dataset when there is no next video frame', async () => {
        const videoFrame = getMockedVideoFrameMediaItem({
            identifier: { videoId: 'test-video-1', type: MEDIA_TYPE.VIDEO_FRAME, frameNumber: 600 },
        });

        // Return only the selected video frame so that submit must select a next media item
        (useVideoPlayerContext as jest.Mock).mockImplementation(() => {
            return { videoFrame, step: 60 };
        });

        const mediaItems = [
            getMockedMediaItem(0),
            { ...videoFrame, metadata: { ...videoFrame.metadata, frames: 600 } },
            getMockedMediaItem(1),
            getMockedMediaItem(2),
            getMockedMediaItem(3),
        ];

        const mediaItem = mediaItems[1];
        const selectMediaItem = jest.fn();
        const submit = {
            mutate: jest.fn(),
        };

        render(
            <App
                mediaItem={mediaItem}
                selectMediaItem={selectMediaItem}
                submitMutation={submit.mutate}
                canSubmit={false}
                newAnnotations={[]}
            />,
            {
                services: {
                    mediaService: createInMemoryMediaService(mediaItems),
                },
            }
        );

        const btn = await screen.findByRole('button', { name: /submit annotations/i });

        await waitFor(async () => {
            expect(btn).toHaveTextContent('Submit »');
            expect(btn).toBeEnabled();
        });

        fireEvent.click(btn);

        await waitFor(() => {
            expect(selectMediaItem).toHaveBeenCalled();
            expect(selectMediaItem).toHaveBeenCalledWith(mediaItems[2]);
        });
    });

    it('Submits "newAnnotations"', async () => {
        const mediaItem = items[1];
        const mediaService = createInMemoryMediaService(items);
        const selectMediaItem = jest.fn();
        const submit = { mutate: jest.fn() };
        jest.mocked(useTaskChainOutput).mockImplementation(() => [userAnnotations]);
        const newAnnotations = [prediction];

        render(
            <App
                mediaItem={mediaItem}
                selectMediaItem={selectMediaItem}
                submitMutation={submit.mutate}
                newAnnotations={newAnnotations}
                canSubmit
            />,
            {
                services: {
                    mediaService,
                },
            }
        );

        const btn = await screen.findByRole('button', { name: /submit annotations/i });
        await waitFor(async () => {
            expect(btn).toHaveTextContent('Accept »');
            expect(btn).toBeEnabled();
        });

        fireEvent.click(btn);

        await waitFor(() => {
            expect(selectMediaItem).toHaveBeenCalledWith(items[2]);
            expect(submit.mutate).toHaveBeenCalledWith({
                annotations: newAnnotations,
                callback: expect.anything(),
            });
        });
    });

    describe('Renders button text', () => {
        const mediaItem = getMockedMediaItem(0, [{ taskId: 'fake-id', state: MEDIA_ANNOTATION_STATUS.NONE }]);
        const mediaService = createInMemoryMediaService([mediaItem]);

        it('only predictions', async () => {
            render(
                <App
                    mediaItem={mediaItem}
                    selectMediaItem={jest.fn()}
                    submitMutation={jest.fn()}
                    newAnnotations={[prediction]}
                    canSubmit
                />,
                {
                    services: {
                        mediaService,
                    },
                }
            );

            const btn = screen.getByRole('button', { name: /submit annotations/i });
            expect(btn).toBeInTheDocument();
            expect(btn).toHaveTextContent('Accept');
        });

        it('prediction and user annotations', async () => {
            jest.mocked(useTaskChainOutput).mockImplementation(() => [prediction, userAnnotations]);

            render(
                <App
                    mediaItem={mediaItem}
                    selectMediaItem={jest.fn()}
                    submitMutation={jest.fn()}
                    newAnnotations={[]}
                    canSubmit
                />,
                {
                    services: {
                        mediaService,
                    },
                }
            );

            const btn = screen.getByRole('button', { name: /submit annotations/i });
            expect(btn).toBeInTheDocument();
            expect(btn).toHaveTextContent('Submit');
        });

        it('only user annotations', async () => {
            jest.mocked(useTaskChainOutput).mockImplementation(() => [userAnnotations]);

            render(
                <App
                    mediaItem={mediaItem}
                    selectMediaItem={jest.fn()}
                    submitMutation={jest.fn()}
                    newAnnotations={[]}
                    canSubmit
                />,
                {
                    services: {
                        mediaService,
                    },
                }
            );

            const btn = screen.getByRole('button', { name: /submit annotations/i });
            expect(btn).toBeInTheDocument();
            expect(btn).toHaveTextContent('Submit');
        });

        it('is disabled while loading media', async () => {
            // @ts-expect-error We only care about mocking the selected media item query
            jest.mocked(useSelectedMediaItem).mockImplementation(() => ({
                selectedMediaItemQuery: { isFetching: true },
            }));

            jest.mocked(useTaskChainOutput).mockImplementation(() => [prediction, userAnnotations]);

            render(
                <App
                    mediaItem={mediaItem}
                    selectMediaItem={jest.fn()}
                    submitMutation={jest.fn()}
                    newAnnotations={[]}
                    canSubmit
                />,
                {
                    services: {
                        mediaService,
                    },
                }
            );

            const btn = screen.getByRole('button', { name: /submit annotations/i });
            expect(btn).toBeInTheDocument();
            expect(btn).toHaveTextContent('Submit');
            expect(btn).toBeDisabled();
        });
    });
});
