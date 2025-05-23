// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ApplicationServicesContextProps } from '@geti/core/src/services/application-services-provider.component';
import { UseQueryResult } from '@tanstack/react-query';
import { screen } from '@testing-library/react';
import { AxiosError } from 'axios';

import { MediaItem } from '../../../../core/media/media.interface';
import { useStatus } from '../../../../core/status/hooks/use-status.hook';
import { TOO_LOW_FREE_DISK_SPACE_IN_BYTES } from '../../../../core/status/hooks/utils';
import { StatusProps } from '../../../../core/status/status.interface';
import { INITIAL_VIEW_MODE, VIEW_MODE_LABEL } from '../../../../shared/components/media-view-modes/utils';
import {
    getMockedImageMediaItem,
    getMockedVideoMediaItem,
} from '../../../../test-utils/mocked-items-factory/mocked-media';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { checkTooltip } from '../../../../test-utils/utils';
import { MediaProvider, useMedia } from '../../../media/providers/media-provider.component';
import { ExportImportDatasetDialogProvider } from '../project-dataset/export-dataset/export-import-dataset-dialog-provider.component';
import { ProjectMediaControlPanel } from './project-media-control-panel.component';
import {
    DELETE_SELECTED_MEDIA_LABEL,
    FILTER_MEDIA_LABEL,
    SEARCH_MEDIA_LABEL,
    SELECT_ALL_LABEL,
    SORT_MEDIA_LABEL,
    UPLOAD_MEDIA_LABEL,
} from './utils';

jest.mock('../../../../core/status/hooks/use-status.hook', () => ({
    ...jest.requireActual('../../../../core/status/hooks/use-status.hook'),
    useStatus: jest.fn(),
}));

jest.mock('../../../media/providers/media-provider.component', () => ({
    ...jest.requireActual('../../../media/providers/media-provider.component'),
    useMedia: jest.fn(() => ({
        media: [],
        mediaSelection: [],
        isMediaFilterEmpty: true,
        sortingOptions: {},
        mediaFilterOptions: {
            condition: 'or',
            rules: [],
        },
    })),
}));

describe('ProjectMediaControlPanel', () => {
    const mediaProps = {
        media: [],
        mediaSelection: [],
        mediaFilterOptions: {
            condition: 'or',
            rules: [],
        },
        isMediaFilterEmpty: true,
        sortingOptions: { sortBy: undefined },
        deleteMedia: { isPending: false, mutate: jest.fn() },
    };

    const renderApp = async (
        isInUploadingState = false,
        isAnomalyProject = false,
        countElements = '',
        services?: Partial<ApplicationServicesContextProps>
    ) => {
        jest.mocked(useStatus).mockReturnValue({
            data: { freeSpace: TOO_LOW_FREE_DISK_SPACE_IN_BYTES + 1, totalSpace: 10, runningJobs: 0 },
        } as UseQueryResult<StatusProps, AxiosError>);

        await render(
            <MediaProvider>
                <ExportImportDatasetDialogProvider>
                    <ProjectMediaControlPanel
                        hasExportImportButtons={!isAnomalyProject}
                        countElements={countElements}
                        uploadMediaCallback={jest.fn}
                        isAnomalyProject={isAnomalyProject}
                        isInUploadingState={isInUploadingState}
                        viewMode={INITIAL_VIEW_MODE}
                        setViewMode={jest.fn()}
                        onCameraSelected={jest.fn()}
                    />
                </ExportImportDatasetDialogProvider>
            </MediaProvider>,
            { services }
        );
    };

    it('select all is disabled when filters are set and there is not media items', async () => {
        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementationOnce(() => ({
            ...mediaProps,
            media: [],
            isMediaFilterEmpty: true,
        }));

        await renderApp();

        expect(screen.queryByRole('checkbox', { name: SELECT_ALL_LABEL })).not.toBeInTheDocument();
    });

    it('all media controls (but delete media) are enabled when there are media items filters are not set', async () => {
        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementationOnce(() => ({
            ...mediaProps,
            media: [getMockedImageMediaItem({})],
            isMediaFilterEmpty: true,
        }));

        await renderApp();

        expect(screen.getByRole('checkbox', { name: SELECT_ALL_LABEL })).toBeEnabled();
        expect(screen.getByRole('button', { name: SEARCH_MEDIA_LABEL })).toBeEnabled();
        expect(screen.getByRole('button', { name: FILTER_MEDIA_LABEL })).toBeEnabled();
        expect(screen.getByRole('button', { name: VIEW_MODE_LABEL })).toBeEnabled();
        expect(screen.getByRole('button', { name: SORT_MEDIA_LABEL })).toBeEnabled();
        expect(screen.getByRole('button', { name: UPLOAD_MEDIA_LABEL })).toBeEnabled();
    });

    it('all media controls (but delete media) are enabled when there are media items and filters are set', async () => {
        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementationOnce(() => ({
            ...mediaProps,
            media: [getMockedImageMediaItem({})],
            isMediaFilterEmpty: false,
        }));

        await renderApp();

        expect(screen.getByRole('checkbox', { name: SELECT_ALL_LABEL })).toBeEnabled();
        expect(screen.getByRole('button', { name: SEARCH_MEDIA_LABEL })).toBeEnabled();
        expect(screen.getByRole('button', { name: FILTER_MEDIA_LABEL })).toBeEnabled();
        expect(screen.getByRole('button', { name: VIEW_MODE_LABEL })).toBeEnabled();
        expect(screen.getByRole('button', { name: SORT_MEDIA_LABEL })).toBeEnabled();
        expect(screen.getByRole('button', { name: UPLOAD_MEDIA_LABEL })).toBeEnabled();
    });

    it('all media controls (but upload media) are disabled while uploading media items', async () => {
        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementationOnce(() => ({
            ...mediaProps,
            media: [getMockedImageMediaItem({})],
            isMediaFilterEmpty: false,
        }));

        await renderApp(true);

        expect(screen.getByRole('checkbox', { name: SELECT_ALL_LABEL })).toBeDisabled();
        expect(screen.getByRole('button', { name: SEARCH_MEDIA_LABEL })).toBeDisabled();
        expect(screen.getByRole('button', { name: FILTER_MEDIA_LABEL })).toBeDisabled();
        expect(screen.getByRole('button', { name: VIEW_MODE_LABEL })).toBeDisabled();
        expect(screen.getByRole('button', { name: SORT_MEDIA_LABEL })).toBeDisabled();
        expect(screen.getByRole('button', { name: UPLOAD_MEDIA_LABEL })).toBeEnabled();
    });

    it('delete media button is visible when there are selected media items', async () => {
        const media = [getMockedImageMediaItem({})];
        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementationOnce(() => ({
            ...mediaProps,
            media,
            mediaSelection: media,
            isMediaFilterEmpty: false,
        }));

        await renderApp();
        const deleteButton = screen.getByRole('button', { name: DELETE_SELECTED_MEDIA_LABEL });
        expect(deleteButton).toBeEnabled();

        await checkTooltip(deleteButton, DELETE_SELECTED_MEDIA_LABEL);
    });

    it('delete media button is not visible when there not selected media items', async () => {
        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementationOnce(() => ({
            ...mediaProps,
            media: [getMockedImageMediaItem({})],
            mediaSelection: [],
            isMediaFilterEmpty: false,
        }));

        await renderApp();

        expect(screen.queryByRole('button', { name: DELETE_SELECTED_MEDIA_LABEL })).not.toBeInTheDocument();
    });

    it('only upload button is enabled when there are no media items and filters are not set', async () => {
        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementationOnce(() => ({
            ...mediaProps,
            media: [],
            isMediaFilterEmpty: true,
        }));

        await renderApp();

        expect(screen.queryByRole('checkbox', { name: SELECT_ALL_LABEL })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: SEARCH_MEDIA_LABEL })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: FILTER_MEDIA_LABEL })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: VIEW_MODE_LABEL })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: SORT_MEDIA_LABEL })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: UPLOAD_MEDIA_LABEL })).not.toBeInTheDocument();
    });

    it('should display message how many media items are selected', async () => {
        const media = [getMockedImageMediaItem({}), getMockedImageMediaItem({}), getMockedImageMediaItem({})];
        const mediaSelection = media.slice(0, 2);
        const totalImages = media.length;
        const totalVideos = 0;

        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementationOnce(() => ({
            ...mediaProps,
            media,
            mediaSelection,
            isMediaFilterEmpty: false,
            totalImages,
            totalVideos,
        }));

        await renderApp();

        expect(screen.getByTestId('selected-items-count-id')).toHaveTextContent(`Selected: ${mediaSelection.length}`);
    });

    it('each media control has a tooltip', async () => {
        const media = [getMockedImageMediaItem({})];
        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementationOnce(() => ({
            ...mediaProps,
            media,
            mediaSelection: [],
            isMediaFilterEmpty: false,
        }));

        await renderApp();

        await checkTooltip(screen.getByRole('checkbox', { name: SELECT_ALL_LABEL }), SELECT_ALL_LABEL);
        await checkTooltip(screen.getByRole('button', { name: SEARCH_MEDIA_LABEL }), SEARCH_MEDIA_LABEL);
        await checkTooltip(screen.getByRole('button', { name: FILTER_MEDIA_LABEL }), FILTER_MEDIA_LABEL);
        await checkTooltip(screen.getByRole('button', { name: VIEW_MODE_LABEL }), VIEW_MODE_LABEL);
        await checkTooltip(screen.getByRole('button', { name: SORT_MEDIA_LABEL }), SORT_MEDIA_LABEL);
    });

    it('should not display how many media items are selected if none of the media is selected', async () => {
        const media = [getMockedImageMediaItem({}), getMockedImageMediaItem({}), getMockedImageMediaItem({})];
        const mediaSelection: MediaItem[] = [];
        const totalImages = media.length;
        const totalVideos = 0;

        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementationOnce(() => ({
            ...mediaProps,
            media,
            mediaSelection,
            isMediaFilterEmpty: false,
            totalImages,
            totalVideos,
        }));

        await renderApp();

        expect(screen.queryByTestId('selected-items-count-id')).not.toBeInTheDocument();
    });

    it('should show "countElements" with no Anomaly projects', async () => {
        const images = [getMockedImageMediaItem({}), getMockedImageMediaItem({}), getMockedImageMediaItem({})];
        const videos = [getMockedVideoMediaItem({}), getMockedVideoMediaItem({})];
        const media = [...images, ...videos];
        const totalImages = images.length;
        const totalVideos = videos.length;

        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementation(() => ({
            ...mediaProps,
            media,
            mediaSelection: media,
            isMediaFilterEmpty: true,
            totalImages,
            totalVideos,
        }));

        const countElements = '4 images';
        await renderApp(false, false, countElements);

        expect(screen.getByTestId('count-message-id')).toHaveTextContent(countElements);
    });
});
