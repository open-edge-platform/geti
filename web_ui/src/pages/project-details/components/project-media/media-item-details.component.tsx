// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useRef, useState } from 'react';

import { Divider, Flex, Grid, minmax, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Checkbox } from '@geti/ui';
import dayjs from 'dayjs';
import { delay } from 'lodash-es';
import { usePress } from 'react-aria';

import { MediaItem } from '../../../../core/media/media.interface';
import { isVideo } from '../../../../core/media/video.interface';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { useOrganizationIdentifier } from '../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { MediaItemView } from '../../../../shared/components/media-item-view/media-item-view.component';
import { PressableElement } from '../../../../shared/components/pressable-element/pressable-element.component';
import { TruncatedText } from '../../../../shared/components/truncated-text/truncated-text.component';
import { getFileSize } from '../../../../shared/utils';
import { getFullNameFromUser } from '../../../user-management/users/users-table/utils';
import { MediaItemActions } from './media-item-actions/media-item-actions.component';
import { VideoDurationDetailsViewIndicator } from './video-item-data-indicator/video-duration-details-view-indicator.component';
import { VideoFrameDetailsViewIndicator } from './video-item-data-indicator/video-frame-details-view-indicator.component';

import classes from './grid-media-item.module.scss';

interface MediaItemDetailsProps {
    id: string;
    isSelected: boolean;
    mediaItem: MediaItem;
    handleDblClick: () => void;
    toggleMediaSelection: () => void;
    shouldShowAnnotationIndicator: boolean;
}

export const MediaItemDetails = ({
    id,
    mediaItem,
    isSelected,
    handleDblClick,
    toggleMediaSelection,
    shouldShowAnnotationIndicator,
}: MediaItemDetailsProps): JSX.Element => {
    const {
        name,
        uploadTime,
        uploaderId,
        metadata: { size },
    } = mediaItem;

    const { organizationId } = useOrganizationIdentifier();
    const { useGetUserQuery } = useUsers();
    const uploaderQuery = useGetUserQuery(organizationId, uploaderId);
    const [selectedMediaItemAction, setSelectedMediaItemAction] = useState<Key | undefined>(undefined);

    const preventSingleClick = useRef<boolean>(false);
    const { pressProps } = usePress({
        onPress: () => {
            // we delay onClick function because we don't want this function to be invoked when user does double click
            delay(() => {
                if (!preventSingleClick.current) {
                    toggleMediaSelection();
                }
            }, 150);
        },
    });

    const onDoubleClick = () => {
        preventSingleClick.current = true;
        handleDblClick();
    };

    const isVideoItem = isVideo(mediaItem);
    const isFilteredVideo = isVideoItem && !!mediaItem.matchedFrames;
    const nameColumnMinWidth = isVideoItem ? (isFilteredVideo ? 'size-3000' : 'size-2000') : 'size-1000';

    const checkBoxColumn = 'size-200';
    const imageColumn = 'size-800';
    const nameColumn = minmax(nameColumnMinWidth, '1fr');
    const dateColumn = 'size-900';
    const fileSizeColumn = minmax('size-500', 'size-1600');
    const uploaderIdColumn = minmax('size-500', 'size-2400');
    const menuColumn = 'size-800';

    const NAME_TOOLTIP = 'Name';
    const FRAMES_TOOLTIP = 'Filtered number of frames';
    const DURATION_TOOLTIP = 'Duration of the video';
    const DATE_TOOLTIP = 'Upload date';
    const FILE_SIZE_TOOLTIP = 'File size';
    const UPLOADER_TOOLTIP = 'Uploader';

    return (
        <Flex direction={'column'} width={'100%'} id={`media-item-${id}-details-id`}>
            <div
                onDoubleClick={onDoubleClick}
                className={[classes.mediaItem, classes.mediaItemDetails].join(' ')}
                {...pressProps}
            >
                <Grid
                    marginX={'size-100'}
                    marginY={'size-100'}
                    gap={'size-200'}
                    alignItems={'center'}
                    justifyContent={'center'}
                    rows={['size-800']}
                    columns={[
                        checkBoxColumn,
                        imageColumn,
                        nameColumn,
                        dateColumn,
                        fileSizeColumn,
                        uploaderIdColumn,
                        menuColumn,
                    ]}
                >
                    <Checkbox
                        id={`select-media-item-${id}-id`}
                        aria-label='Select media item'
                        isSelected={isSelected}
                        onChange={toggleMediaSelection}
                    />
                    <MediaItemView
                        mediaItem={mediaItem}
                        shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                        shouldShowVideoIndicator={false}
                    />

                    <Flex
                        width={'100%'}
                        gap={'size-100'}
                        UNSAFE_className={classes.itemDetailsColumn}
                        alignItems={'center'}
                    >
                        <Flex
                            direction={'column'}
                            width={'100%'}
                            UNSAFE_className={`${classes.nameField} ${
                                isFilteredVideo ? classes.filteredVideo : isVideoItem ? classes.video : ''
                            }`}
                        >
                            <TooltipTrigger placement={'bottom'}>
                                <PressableElement>
                                    <TruncatedText>{name}</TruncatedText>
                                </PressableElement>
                                <Tooltip>{`${NAME_TOOLTIP}: ${name}`}</Tooltip>
                            </TooltipTrigger>
                        </Flex>
                        <Flex gap={'size-100'} alignItems={'center'}>
                            {isVideoItem && (
                                <>
                                    {isFilteredVideo && (
                                        <VideoFrameDetailsViewIndicator
                                            frames={mediaItem.matchedFrames as number}
                                            tooltip={FRAMES_TOOLTIP}
                                        />
                                    )}

                                    <VideoDurationDetailsViewIndicator
                                        duration={mediaItem.metadata.duration}
                                        tooltip={DURATION_TOOLTIP}
                                    />
                                </>
                            )}
                        </Flex>
                    </Flex>

                    <TooltipTrigger placement={'bottom'}>
                        <PressableElement width={'size-1000'}>
                            {dayjs(uploadTime).format('DD.MM.YYYY')}
                        </PressableElement>
                        <Tooltip>{`${DATE_TOOLTIP}: ${dayjs(uploadTime).format('DD.MM.YYYY')}`}</Tooltip>
                    </TooltipTrigger>

                    <TooltipTrigger placement={'bottom'}>
                        <PressableElement>
                            <TruncatedText UNSAFE_className={classes.textCenter}>{getFileSize(size)}</TruncatedText>
                        </PressableElement>
                        <Tooltip>{`${FILE_SIZE_TOOLTIP}: ${getFileSize(size)}`}</Tooltip>
                    </TooltipTrigger>

                    <TooltipTrigger placement={'bottom'}>
                        <PressableElement>
                            <TruncatedText UNSAFE_className={classes.textCenter}>
                                {getFullNameFromUser(uploaderQuery.data)}
                            </TruncatedText>
                        </PressableElement>
                        <Tooltip>{`${UPLOADER_TOOLTIP}: ${getFullNameFromUser(uploaderQuery.data)}`}</Tooltip>
                    </TooltipTrigger>

                    <MediaItemActions
                        mediaItem={mediaItem}
                        selectedMediaItemAction={selectedMediaItemAction}
                        onSelectedMediaItemActionChange={setSelectedMediaItemAction}
                    />
                </Grid>
            </div>
            <Divider size={'S'} width={'100%'} />
        </Flex>
    );
};
