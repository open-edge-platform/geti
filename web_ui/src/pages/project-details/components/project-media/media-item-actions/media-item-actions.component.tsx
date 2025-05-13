// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key } from 'react';

import { DialogContainer, Flex, Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { Scope } from '../../../../../assets/icons';
import { useFeatureFlags } from '../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { MediaIdentifier, MediaItem } from '../../../../../core/media/media.interface';
import { isVideo, isVideoFrame } from '../../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../../core/projects/dataset.interface';
import { isAnomalyDomain, isClassificationDomain } from '../../../../../core/projects/domains';
import { MediaItemMenuActions } from '../../../../../shared/components/media-item-menu-with-deletion/media-item-menu-actions.enum';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { VideoPlayerDialog } from '../../../../annotator/components/range-based-video-player/video-player-dialog.component';
import { useDatasetIdentifier } from '../../../../annotator/hooks/use-dataset-identifier.hook';
import { useMediaItemQuery } from '../../../../annotator/providers/selected-media-item-provider/use-media-item-query.hook';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { MediaItemMenu } from './media-item-menu.component';

const useVideoMediaItemQuery = (datasetIdentifier: DatasetIdentifier, mediaItem: MediaItem) => {
    const videoId: MediaIdentifier | undefined = isVideo(mediaItem)
        ? mediaItem.identifier
        : isVideoFrame(mediaItem)
          ? {
                type: MEDIA_TYPE.VIDEO,
                videoId: mediaItem.identifier.videoId,
            }
          : undefined;

    return useMediaItemQuery(datasetIdentifier, videoId, {
        enabled: isVideoFrame(mediaItem),
        placeholderData: isVideo(mediaItem) ? mediaItem : undefined,
    });
};

interface QuickAnnotationButtonProps {
    onClick: () => void;
}

const QuickAnnotationButton: FC<QuickAnnotationButtonProps> = ({ onClick }) => {
    return (
        <TooltipTrigger>
            <QuietActionButton onPress={onClick} aria-label={'Quick annotation'}>
                <Scope />
            </QuietActionButton>
            <Tooltip>
                <Text>Quick annotation</Text>
            </Tooltip>
        </TooltipTrigger>
    );
};

interface MediaItemActionsProps {
    mediaItem: MediaItem;
    selectedMediaItemAction: Key | undefined;
    onSelectedMediaItemActionChange: (action: Key | undefined) => void;
}

export const MediaItemActions: FC<MediaItemActionsProps> = ({
    mediaItem,
    selectedMediaItemAction,
    onSelectedMediaItemActionChange,
}) => {
    const { FEATURE_FLAG_CLASSIFICATION_RANGES } = useFeatureFlags();
    const { isSingleDomainProject } = useProject();

    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);
    const isClassificationProject = isSingleDomainProject(isClassificationDomain);
    const datasetIdentifier = useDatasetIdentifier();
    const videoMediaItemQuery = useVideoMediaItemQuery(datasetIdentifier, mediaItem);
    const isVideoMediaItem = isVideo(mediaItem);
    const videoMediaItemForDialog = isVideoMediaItem ? mediaItem : videoMediaItemQuery.data;
    const shouldShowQuickAnnotation =
        isVideoMediaItem &&
        videoMediaItemForDialog !== undefined &&
        (isAnomalyProject || (isClassificationProject && FEATURE_FLAG_CLASSIFICATION_RANGES));

    const isAnomalyVideo = isAnomalyProject && videoMediaItemForDialog !== undefined;

    if (shouldShowQuickAnnotation) {
        const handleOpenQuickAnnotation = () =>
            onSelectedMediaItemActionChange(MediaItemMenuActions.QUICK_ANNOTATION.toLocaleLowerCase());

        const handleCloseDialog = () => onSelectedMediaItemActionChange(undefined);

        return (
            <Flex alignItems={'center'}>
                <QuickAnnotationButton onClick={handleOpenQuickAnnotation} />
                <MediaItemMenu
                    mediaItem={mediaItem}
                    showQuickAnnotation
                    isAnomalyVideo={isAnomalyVideo}
                    selectedMediaItemAction={selectedMediaItemAction}
                    onChangeSelectedMediaItemAction={onSelectedMediaItemActionChange}
                />
                <DialogContainer onDismiss={handleCloseDialog}>
                    {selectedMediaItemAction === MediaItemMenuActions.QUICK_ANNOTATION.toLowerCase() &&
                        isVideo(videoMediaItemForDialog) && (
                            <VideoPlayerDialog
                                datasetIdentifier={datasetIdentifier}
                                mediaItem={videoMediaItemForDialog}
                                close={handleCloseDialog}
                            />
                        )}
                </DialogContainer>
            </Flex>
        );
    }

    return (
        <MediaItemMenu
            mediaItem={mediaItem}
            showQuickAnnotation={false}
            isAnomalyVideo={isAnomalyVideo}
            selectedMediaItemAction={selectedMediaItemAction}
            onChangeSelectedMediaItemAction={onSelectedMediaItemActionChange}
        />
    );
};
