// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, FC, ReactNode, SVGProps } from 'react';

import { Divider, Flex, IllustratedMessage, View } from '@adobe/react-spectrum';
import { useMediaQuery } from '@react-spectrum/utils';
import { DimensionValue } from '@react-types/shared/src/dna';
import { Responsive } from '@react-types/shared/src/style';
import { MediaDropBoxHeader } from '@shared/components/media-drop/media-drop-box-header.component';
import { MediaDropBox } from '@shared/components/media-drop/media-drop-box.component';
import { MediaItemsList } from '@shared/components/media-items-list/media-items-list.component';
import { INITIAL_VIEW_MODE } from '@shared/components/media-view-modes/utils';
import { TutorialCardBuilder } from '@shared/components/tutorial-card/tutorial-card-builder.component';
import { VALID_MEDIA_TYPES_DISPLAY } from '@shared/media-utils';
import NotFound from '@spectrum-icons/illustrations/NotFound';
import isEmpty from 'lodash/isEmpty';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { isKeypointTask } from '../../../../core/projects/utils';
import { TUTORIAL_CARD_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useViewMode } from '../../../../hooks/use-view-mode/use-view-mode.hook';
import { DatasetMediaUploadActions } from '../../../../providers/media-upload-provider/media-upload-reducer-actions';
import {
    MEDIA_CONTENT_BUCKET,
    MediaUploadPerDataset,
} from '../../../../providers/media-upload-provider/media-upload.interface';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { MediaFilterChips } from '../../../media/components/media-filter-chips.component';
import { useMedia } from '../../../media/providers/media-provider.component';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { getMatchedMediaCounts, getTotalMediaCounts } from '../../utils';
import { AnomalyMediaHeaderInformation } from './anomaly-media-header-information.component';
import { DeletionStatusBar } from './deletion-status-bar.component';
import { LoadingOverlay } from './loading-overlay.component';
import { MediaItemFactory } from './media-item-factory.component';
import { ProjectMediaControlPanel } from './project-media-control-panel.component';
import { getUploadingStatePerBucket } from './utils';

interface UploadMediaMetaData {
    mediaUploadState: MediaUploadPerDataset;
    dispatch: Dispatch<DatasetMediaUploadActions>;
}

export interface MediaContentBucketProps {
    header?: string;
    description?: string;
    DropBoxIcon?: FC<SVGProps<SVGSVGElement>>;
    contentBucketClass?: string;
    contentBucketBodyClass?: string;
    dropBoxIconSize?: Responsive<DimensionValue>;
    mediaBucket: MEDIA_CONTENT_BUCKET;
    uploadMediaMetadata: UploadMediaMetaData;
    onCameraSelected: () => void;
    handleUploadMediaCallback: (files: File[]) => void;
    isLoadingOverlayVisible: (isMediaFetching: boolean) => boolean;
    isMediaDropVisible: (isMediaFetching: boolean, hasMediaItems: boolean, isMediaFilterEmpty: boolean) => boolean;
    showExportImportButton?: boolean;
    footerInfo?: ReactNode;
}

export const MediaContentBucket = ({
    header,
    description,
    footerInfo,
    mediaBucket,
    DropBoxIcon,
    dropBoxIconSize,
    uploadMediaMetadata,
    contentBucketClass = '',
    contentBucketBodyClass = '',
    onCameraSelected,
    isMediaDropVisible,
    showExportImportButton,
    isLoadingOverlayVisible,
    handleUploadMediaCallback,
}: MediaContentBucketProps): JSX.Element => {
    const { project } = useProject();
    const isAnomalyProject = mediaBucket !== MEDIA_CONTENT_BUCKET.GENERIC;
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const { FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE } = useFeatureFlags();
    const [viewMode, setViewMode] = useViewMode(mediaBucket, INITIAL_VIEW_MODE);

    const {
        media,
        isLoading,
        loadNextMedia,
        totalImages,
        totalVideos,
        isMediaFetching,
        isFetchingNextPage,
        isMediaFilterEmpty,
        totalMatchedVideos,
        totalMatchedImages,
        isDeletionInProgress,
        totalMatchedVideoFrames,
        mediaFilterOptions,
        setMediaFilterOptions,
        mediaSelection,
        toggleItemInMediaSelection,
    } = useMedia();

    const hasMediaItems = !isEmpty(media);
    const bucketId = idMatchingFormat(mediaBucket);
    const shouldShowMediaDrop = isMediaDropVisible(isMediaFetching, hasMediaItems, isMediaFilterEmpty);
    const shouldShowLoadingOverlay = isLoadingOverlayVisible(isMediaFetching || isLoading);

    const { uploadProgress, isUploadInProgress } = uploadMediaMetadata.mediaUploadState;

    const acceptedFormats = VALID_MEDIA_TYPES_DISPLAY;
    const isHeaderInfoEnabled = header && description;
    const isControlPanelVisible = hasMediaItems || !isMediaFilterEmpty;
    const shouldShowHeader = isAnomalyProject && isControlPanelVisible && isHeaderInfoEnabled;

    const isKeypointIeEnabled = project.tasks.some(isKeypointTask) ? FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE : true;

    const countElements = isMediaFilterEmpty
        ? getTotalMediaCounts(
              isAnomalyProject ? totalMatchedImages : totalImages,
              isAnomalyProject ? totalMatchedVideos : totalVideos
          )
        : getMatchedMediaCounts(totalMatchedImages, totalMatchedVideoFrames, totalMatchedVideos);

    return (
        <Flex
            UNSAFE_className={contentBucketClass}
            id={`${bucketId}-content-id`}
            data-testid={`${bucketId}-content-id`}
            width={'100%'}
            direction={'column'}
            gap={'size-100'}
        >
            {(!isAnomalyProject || shouldShowHeader) && (
                <View>
                    {!isAnomalyProject && <TutorialCardBuilder cardKey={TUTORIAL_CARD_KEYS.PROJECT_DATASET_TUTORIAL} />}
                    {shouldShowHeader && (
                        <AnomalyMediaHeaderInformation
                            description={description}
                            countElements={countElements}
                            headerText={header}
                        />
                    )}
                </View>
            )}
            <Flex flex={1} gap='size-100' direction='column' UNSAFE_className={contentBucketBodyClass}>
                {isControlPanelVisible && (
                    <ProjectMediaControlPanel
                        viewMode={viewMode}
                        countElements={countElements}
                        isAnomalyProject={isAnomalyProject}
                        hasExportImportButtons={!isAnomalyProject && isKeypointIeEnabled}
                        setViewMode={setViewMode}
                        onCameraSelected={onCameraSelected}
                        uploadMediaCallback={handleUploadMediaCallback}
                        isInUploadingState={getUploadingStatePerBucket(uploadProgress, mediaBucket)}
                    />
                )}

                {isControlPanelVisible && <Divider size='S' />}

                <MediaFilterChips
                    labels={project.labels}
                    isAnomalyProject={isAnomalyProject}
                    mediaFilterOptions={mediaFilterOptions}
                    setMediaFilterOptions={setMediaFilterOptions}
                />

                <MediaDropBox
                    DropBoxIcon={DropBoxIcon}
                    dropBoxIconSize={dropBoxIconSize}
                    isVisible={shouldShowMediaDrop}
                    onCameraSelected={onCameraSelected}
                    onDrop={handleUploadMediaCallback}
                    showUploadButton={!media.length}
                    showExportImportButton={showExportImportButton}
                    headerInfo={
                        !hasMediaItems && isHeaderInfoEnabled
                            ? {
                                  header,
                                  countElements: !isEmpty(media) ? countElements : undefined,
                                  description,
                              }
                            : undefined
                    }
                    acceptedFormats={acceptedFormats}
                    footerInfo={footerInfo}
                    dropBoxHeader={
                        <MediaDropBoxHeader formats={acceptedFormats} bucket={mediaBucket} isMultipleUpload />
                    }
                    multiple
                >
                    <Flex height='100%' direction='column' position={'relative'}>
                        {hasMediaItems && (
                            <MediaItemsList
                                id={`media-${bucketId}-dataset-list`}
                                endReached={() => loadNextMedia(false)}
                                totalCount={media.length}
                                viewMode={viewMode}
                                itemContent={(index) => (
                                    <MediaItemFactory
                                        mediaItem={media[index]}
                                        viewMode={viewMode}
                                        isLargeSize={isLargeSize}
                                        mediaSelection={mediaSelection}
                                        toggleItemInMediaSelection={toggleItemInMediaSelection}
                                        shouldShowAnnotationIndicator
                                    />
                                )}
                            />
                        )}

                        <IllustratedMessage
                            isHidden={
                                isUploadInProgress ||
                                isMediaFetching ||
                                hasMediaItems ||
                                shouldShowMediaDrop ||
                                (hasMediaItems && !isMediaDropVisible) ||
                                (hasMediaItems && !isMediaFilterEmpty)
                            }
                        >
                            <NotFound />
                        </IllustratedMessage>

                        <LoadingOverlay
                            id={
                                header
                                    ? `media-gallery-loading-overlay-${header.toLowerCase()}-id`
                                    : 'media-gallery-loading-overlay-id'
                            }
                            size={'M'}
                            backgroundColor={isFetchingNextPage ? 'transparent' : 'gray-50'}
                            fetchingNextPage={isFetchingNextPage}
                            visible={shouldShowLoadingOverlay || isFetchingNextPage}
                        />
                    </Flex>
                </MediaDropBox>

                <DeletionStatusBar visible={isDeletionInProgress} />
            </Flex>
        </Flex>
    );
};
