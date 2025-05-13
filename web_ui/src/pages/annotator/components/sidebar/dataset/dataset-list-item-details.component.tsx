// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, useMemo } from 'react';

import { Divider, Flex, Grid, minmax, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { isEmpty } from 'lodash-es';
import { usePress } from 'react-aria';

import { isVideo } from '../../../../../core/media/video.interface';
import { useUsers } from '../../../../../core/users/hook/use-users.hook';
import { useOrganizationIdentifier } from '../../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { MediaItemView } from '../../../../../shared/components/media-item-view/media-item-view.component';
import { PressableElement } from '../../../../../shared/components/pressable-element/pressable-element.component';
import { TruncatedTextWithTooltip } from '../../../../../shared/components/truncated-text/truncated-text.component';
import { getFileSize } from '../../../../../shared/utils';
import { getMediaId } from '../../../../media/utils';
import { DatasetListItemVideoDetails } from './dataset-list-item-video-details.component';
import { DatasetListItem } from './dataset-list-item.component';
import { formatUploadTime } from './utils';

import classes from './dataset-list-item-details.module.scss';

export const DatasetListItemDetails = ({
    mediaItem,
    isSelected,
    datasetItemMenu,
    selectMediaItem,
    shouldShowAnnotationIndicator,
}: ComponentProps<typeof DatasetListItem>): JSX.Element => {
    const { pressProps } = usePress({ onPress: selectMediaItem });
    const {
        name,
        uploadTime,
        metadata: { size },
        lastAnnotatorId,
    } = mediaItem;

    const { organizationId } = useOrganizationIdentifier();
    const { useGetUserQuery } = useUsers();
    const userQuery = useGetUserQuery(organizationId, lastAnnotatorId ?? undefined);
    const lastAnnotator = userQuery.data;

    const id = getMediaId(mediaItem);

    const columns: ComponentProps<typeof Grid>['columns'] = useMemo(() => {
        const initialColumns = ['size-800', minmax('size-1000', '1fr')];

        if (datasetItemMenu !== undefined) {
            initialColumns.push('max-content');
        }

        return initialColumns;
    }, [datasetItemMenu]);

    return (
        <>
            <div
                id={id}
                data-testid={id}
                className={`${classes.itemDetails} ${isSelected ? classes.itemDetailsSelected : ''}`}
                {...pressProps}
            >
                <Grid
                    columns={columns}
                    width={'100%'}
                    gap={'size-100'}
                    alignItems={'center'}
                    justifyContent={'center'}
                    rows={['size-800']}
                >
                    <View justifySelf={'start'}>
                        <MediaItemView
                            mediaItem={mediaItem}
                            shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                            shouldShowVideoIndicator={false}
                        />
                    </View>
                    <Flex direction={'column'} width={'100%'}>
                        <TooltipTrigger placement={'bottom'}>
                            <PressableElement UNSAFE_className={classes.itemMediaName}>{name}</PressableElement>
                            <Tooltip>{name}</Tooltip>
                        </TooltipTrigger>

                        <Text UNSAFE_className={classes.itemDetailsText}>
                            {`${formatUploadTime(uploadTime)} | ${getFileSize(size)}`}
                        </Text>

                        {!isEmpty(lastAnnotator) && lastAnnotator.firstName && (
                            <TruncatedTextWithTooltip UNSAFE_className={classes.itemDetailsText}>
                                {lastAnnotator.firstName}
                            </TruncatedTextWithTooltip>
                        )}
                        {isVideo(mediaItem) && (
                            <DatasetListItemVideoDetails
                                className={classes.itemDetailsText}
                                duration={mediaItem.metadata.duration}
                                frames={mediaItem.matchedFrames}
                            />
                        )}
                    </Flex>

                    {datasetItemMenu}
                </Grid>
            </div>
            <Divider size={'S'} UNSAFE_className={classes.itemDetailsDivider} />
        </>
    );
};
