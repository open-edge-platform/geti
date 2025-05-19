// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useState } from 'react';

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { MediaItem } from '../../../../../core/media/media.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { ProjectService } from '../../../../../core/projects/services/project-service.interface';
import { MediaItemMenuActions } from '../../../../../shared/components/media-item-menu-with-deletion/media-item-menu-actions.enum';
import { getMockedVideoMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender } from '../../../../../test-utils/project-provider-render';
import { MediaProvider, useMedia } from '../../../../media/providers/media-provider.component';
import { DELETE_ANOMALY_VIDEO_WARNING } from '../media-item-tooltip-message/utils';
import { MediaItemActions } from './media-item-actions.component';

const mockInvalidateQueries = jest.fn();
jest.mock('@tanstack/react-query', () => ({
    ...jest.requireActual('@tanstack/react-query'),
    useQueryClient: () => ({ invalidateQueries: mockInvalidateQueries }),
}));

const mockDeleteMedia = {
    mutate: jest.fn(() => Promise.resolve()),
};

const mockLoadNextMedia = jest.fn();

jest.mock('../../../../media/providers/media-provider.component', () => ({
    ...jest.requireActual('../../../../media/providers/media-provider.component'),
    useMedia: jest.fn(() => ({ deleteMedia: mockDeleteMedia, loadNextMedia: mockLoadNextMedia })),
}));

const mockVideo: MediaItem = getMockedVideoMediaItem({});

describe('MediaItemActions', () => {
    const App = ({ mediaItem }: { mediaItem: MediaItem }) => {
        const [selectedMediaItemAction, setSelectedMediaItemAction] = useState<Key | undefined>(undefined);

        return (
            <MediaItemActions
                mediaItem={mediaItem}
                selectedMediaItemAction={selectedMediaItemAction}
                onSelectedMediaItemActionChange={setSelectedMediaItemAction}
            />
        );
    };

    const renderApp = async ({
        mediaItem,
        projectService = createInMemoryProjectService(),
        FEATURE_FLAG_CLASSIFICATION_RANGES = false,
    }: {
        mediaItem: MediaItem;
        projectService?: ProjectService;
        FEATURE_FLAG_CLASSIFICATION_RANGES?: boolean;
    }) => {
        return projectRender(
            <MediaProvider>
                <App mediaItem={mediaItem} />
            </MediaProvider>,
            { services: { projectService }, featureFlags: { FEATURE_FLAG_CLASSIFICATION_RANGES } }
        );
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('Show common menu items and quick annotation for anomaly', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProject = jest
            .fn()
            .mockResolvedValue(getMockedProject({ tasks: [getMockedTask({ domain: DOMAIN.ANOMALY_CLASSIFICATION })] }));

        await renderApp({ mediaItem: mockVideo, projectService });

        fireEvent.click(screen.getByRole('button', { name: 'open menu' }));
        Object.values(MediaItemMenuActions).forEach((menuAction) => {
            expect(screen.getByRole('menuitem', { name: menuAction })).toBeInTheDocument();
        });
    });

    it('Show common menu items and quick annotation for classification', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProject = jest
            .fn()
            .mockResolvedValue(getMockedProject({ tasks: [getMockedTask({ domain: DOMAIN.CLASSIFICATION })] }));

        await renderApp({ mediaItem: mockVideo, projectService, FEATURE_FLAG_CLASSIFICATION_RANGES: true });

        fireEvent.click(screen.getByRole('button', { name: 'open menu' }));
        Object.values(MediaItemMenuActions).forEach((menuAction) => {
            expect(screen.getByRole('menuitem', { name: menuAction })).toBeInTheDocument();
        });
    });

    it('Displays quick annotation', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProject = jest
            .fn()
            .mockResolvedValue(getMockedProject({ tasks: [getMockedTask({ domain: DOMAIN.CLASSIFICATION })] }));

        await renderApp({ mediaItem: mockVideo, projectService, FEATURE_FLAG_CLASSIFICATION_RANGES: true });

        expect(screen.getByRole('button', { name: 'Quick annotation' })).toBeVisible();

        fireEvent.click(screen.getByRole('button', { name: 'Quick annotation' }));

        expect(await screen.findByRole('heading', { name: /Quick annotation/i })).toBeInTheDocument();
    });

    it('Renders menu options for not anomaly project', async () => {
        await renderApp({ mediaItem: mockVideo });

        fireEvent.click(screen.getByRole('button', { name: 'open menu' }));
        expect(screen.getByRole('menuitem', { name: MediaItemMenuActions.DELETE })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: MediaItemMenuActions.ANNOTATE })).toBeInTheDocument();
        expect(screen.queryByRole('menuitem', { name: MediaItemMenuActions.QUICK_ANNOTATION })).not.toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: MediaItemMenuActions.DOWNLOAD })).toBeInTheDocument();
    });

    it('Deletes anomaly video', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProject = jest
            .fn()
            .mockResolvedValue(getMockedProject({ tasks: [getMockedTask({ domain: DOMAIN.ANOMALY_CLASSIFICATION })] }));

        const mockDeleteMedia2 = {
            mutate: jest.fn(() => mockInvalidateQueries()),
        };

        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementation(() => ({
            deleteMedia: mockDeleteMedia2,
        }));

        await renderApp({ mediaItem: mockVideo, projectService });

        fireEvent.click(screen.getByRole('button', { name: 'open menu' }));
        fireEvent.click(screen.getByRole('menuitem', { name: MediaItemMenuActions.DELETE }));
        expect(screen.queryByText(DELETE_ANOMALY_VIDEO_WARNING)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

        await waitFor(() => {
            expect(mockLoadNextMedia).not.toHaveBeenCalled();
            expect(mockDeleteMedia2.mutate).toHaveBeenCalled();
            expect(mockInvalidateQueries).toHaveBeenCalled();
        });
    });

    it('Deletes video', async () => {
        const mockDeleteMedia2 = {
            mutate: jest.fn(async () => mockLoadNextMedia(true)),
        };

        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementation(() => ({
            deleteMedia: mockDeleteMedia2,
            loadNextMedia: mockLoadNextMedia,
        }));

        await renderApp({ mediaItem: mockVideo });

        fireEvent.click(screen.getByRole('button', { name: 'open menu' }));
        fireEvent.click(screen.getByRole('menuitem', { name: MediaItemMenuActions.DELETE }));
        expect(screen.queryByText(DELETE_ANOMALY_VIDEO_WARNING)).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

        await waitFor(() => {
            expect(mockLoadNextMedia).toHaveBeenCalledWith(true);
            expect(mockDeleteMedia2.mutate).toHaveBeenCalled();
            expect(mockInvalidateQueries).not.toHaveBeenCalled();
        });
    });
});
