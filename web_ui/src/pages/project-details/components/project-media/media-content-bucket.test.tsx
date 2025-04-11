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

import { screen, waitFor } from '@testing-library/react';

import { FeatureFlags } from '../../../../core/feature-flags/services/feature-flag-service.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { ApplicationServicesContextProps } from '../../../../core/services/application-services-provider.component';
import { useDeploymentConfigQuery } from '../../../../core/services/use-deployment-config-query.hook';
import {
    MEDIA_CONTENT_BUCKET,
    MediaUploadPerDataset,
} from '../../../../providers/media-upload-provider/media-upload.interface';
import {
    getMockedImageMediaItem,
    getMockedVideoMediaItem,
} from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { projectRender } from '../../../../test-utils/project-provider-render';
import { MediaProvider, useMedia } from '../../../media/providers/media-provider.component';
import { getMatchedMediaCounts, getTotalMediaCounts } from '../../utils';
import { ExportImportDatasetDialogProvider } from '../project-dataset/export-dataset/export-import-dataset-dialog-provider.component';
import { MediaContentBucket, MediaContentBucketProps } from './media-content-bucket.component';

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

jest.mock('../../../../core/services/use-deployment-config-query.hook', () => ({
    ...jest.requireActual('../../../../core/services/use-deployment-config-query.hook'),
    useDeploymentConfigQuery: jest.fn(),
}));

describe('MediaContentBucket', () => {
    const mockedImage = getMockedImageMediaItem({});
    const mockedVideo = getMockedVideoMediaItem({});

    const mockedUseDeploymentConfigQueryData = {
        servingMode: 'on-prem',
        auth: {
            type: 'dex',
            clientId: 'web_ui',
            authority: '/dex',
        },
        controlPlaneUrl: null,
        dataPlaneUrl: null,
        docsUrl: 'https://docs.geti.intel.com/on-prem/2.6/',
    } as const;

    beforeEach(() => {
        // @ts-expect-error We only use data
        jest.mocked(useDeploymentConfigQuery).mockReturnValue({ data: mockedUseDeploymentConfigQueryData });
    });

    afterEach(() => {
        jest.resetAllMocks();
    });

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

    const renderApp = async ({
        isAnomalyProject = false,
        services,
        bucketProps,
        featureFlags,
    }: {
        isAnomalyProject?: boolean;
        featureFlags?: Partial<FeatureFlags>;
        services?: Partial<ApplicationServicesContextProps>;
        bucketProps?: Partial<MediaContentBucketProps>;
    }) => {
        const mediaBucket = isAnomalyProject ? MEDIA_CONTENT_BUCKET.ANOMALOUS : MEDIA_CONTENT_BUCKET.GENERIC;
        await projectRender(
            <MediaProvider>
                <ExportImportDatasetDialogProvider>
                    <MediaContentBucket
                        DropBoxIcon={undefined}
                        onCameraSelected={jest.fn()}
                        uploadMediaMetadata={{
                            dispatch: jest.fn(),
                            mediaUploadState: {
                                uploadProgress: {},
                                isUploadInProgress: false,
                                isUploadStatusBarVisible: false,
                            } as unknown as MediaUploadPerDataset,
                        }}
                        description='Normal images are used for training'
                        header={'Some header'}
                        dropBoxIconSize='size-2400'
                        mediaBucket={mediaBucket}
                        isMediaDropVisible={jest.fn()}
                        isLoadingOverlayVisible={jest.fn()}
                        handleUploadMediaCallback={jest.fn()}
                        {...bucketProps}
                    />
                </ExportImportDatasetDialogProvider>
            </MediaProvider>,
            { services, featureFlags }
        );
    };

    it('should show default count if there are media items without filters', async () => {
        const images = [mockedImage, mockedImage, mockedImage];
        const videos = [mockedVideo, mockedVideo];
        const media = [...images, ...videos];
        const totalImages = images.length;
        const totalVideos = videos.length;

        //@ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementation(() => ({
            ...mediaProps,
            media,
            mediaSelection: media,
            isMediaFilterEmpty: true,
            totalImages,
            totalVideos,
        }));

        await renderApp({});

        await waitFor(() => {
            expect(screen.getByTestId('count-message-id')).toHaveTextContent(
                getTotalMediaCounts(totalImages, totalVideos)
            );
        });
    });

    it('should show default count for images if there are only images without filters', async () => {
        const media = [mockedImage, mockedImage, mockedImage];
        const totalImages = media.length;
        const totalVideos = 0;

        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementation(() => ({
            ...mediaProps,
            media,
            mediaSelection: media,
            isMediaFilterEmpty: true,
            totalImages,
            totalVideos,
        }));

        await renderApp({});

        await waitFor(() => {
            expect(screen.getByTestId('count-message-id')).toHaveTextContent(
                getTotalMediaCounts(totalImages, totalVideos)
            );
        });
    });

    it('Anomaly project - should show matched count if there are media items', async () => {
        const images = [mockedImage, mockedImage, mockedImage];
        const videos = [mockedVideo, mockedVideo];
        const media = [...images, ...videos];
        const totalImages = images.length;
        const totalVideos = videos.length;

        const projectService = createInMemoryProjectService();
        projectService.getProject = jest.fn(async () => getMockedProject({ domains: [DOMAIN.ANOMALY_CLASSIFICATION] }));

        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementation(() => ({
            ...mediaProps,
            media,
            mediaSelection: media,
            isMediaFilterEmpty: true,
            totalImages,
            totalVideos,
            totalMatchedImages: totalImages,
            totalMatchedVideos: totalVideos,
        }));

        await renderApp({ isAnomalyProject: true, services: { projectService } });

        expect(screen.getByTestId('count-message-id')).toHaveTextContent(getTotalMediaCounts(totalImages, totalVideos));
    });

    it('should show matched count if there are media items with filters', async () => {
        const images = [mockedImage, mockedImage, mockedImage];
        const videos = [mockedVideo, mockedVideo];
        const media = [...images, ...videos];
        const totalImages = images.length;
        const totalVideos = videos.length;
        const totalMatchedImages = totalImages - 1;
        const totalMatchedVideos = totalVideos - 1;
        const totalMatchedVideoFrames = totalVideos - 1;

        // @ts-expect-error we are not interested in other media props
        jest.mocked(useMedia).mockImplementation(() => ({
            ...mediaProps,
            media,
            mediaSelection: media,
            isMediaFilterEmpty: false,
            totalImages,
            totalVideos,
            totalMatchedImages,
            totalMatchedVideos,
            totalMatchedVideoFrames,
        }));

        await renderApp({});

        expect(screen.getByTestId('count-message-id')).toHaveTextContent(
            getMatchedMediaCounts(totalMatchedImages, totalMatchedVideoFrames, totalMatchedVideos)
        );
    });

    describe('import/export button', () => {
        beforeEach(() => {
            const images = [mockedImage, mockedImage, mockedImage];
            const videos = [mockedVideo, mockedVideo];
            const media = [...images, ...videos];
            const totalImages = images.length;
            const totalVideos = videos.length;
            const totalMatchedImages = totalImages - 1;
            const totalMatchedVideos = totalVideos - 1;
            const totalMatchedVideoFrames = totalVideos - 1;

            // @ts-expect-error we are not interested in other media props
            jest.mocked(useMedia).mockImplementation(() => ({
                ...mediaProps,
                media,
                mediaSelection: [],
                isMediaFilterEmpty: false,
                totalImages,
                totalVideos,
                totalMatchedImages,
                totalMatchedVideos,
                totalMatchedVideoFrames,
            }));
        });

        it('visible for non-anomaly and non-keypoint projects even if the flag is off', async () => {
            await renderApp({
                isAnomalyProject: false,
                featureFlags: { FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE: false },
            });

            expect(screen.queryByRole('button', { name: 'Export or import dataset' })).toBeVisible();
        });

        it('hidden for anomaly projects', async () => {
            await renderApp({ isAnomalyProject: true });

            expect(screen.queryByRole('button', { name: 'Export or import dataset' })).not.toBeInTheDocument();
        });

        it('hidden for keypoint projects when the FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE is off', async () => {
            const projectService = createInMemoryProjectService();
            projectService.getProject = jest.fn(async () => getMockedProject({ domains: [DOMAIN.KEYPOINT_DETECTION] }));

            await renderApp({
                isAnomalyProject: false,
                services: { projectService },
                featureFlags: { FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE: false },
            });

            expect(screen.queryByRole('button', { name: 'Export or import dataset' })).not.toBeInTheDocument();
        });
    });
});
