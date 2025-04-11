// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentProps, useMemo } from 'react';

import { Divider, Flex, Grid, minmax, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import { usePress } from 'react-aria';

import { isVideo } from '../../../../../core/media/video.interface';
import { useUsers } from '../../../../../core/users/hook/use-users.hook';
import { useOrganizationIdentifier } from '../../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { ActionElement } from '../../../../../shared/components/action-element/action-element.component';
import { MediaItemView } from '../../../../../shared/components/media-item-view/media-item-view.component';
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
        const initialColumns = ['var(--width)', minmax('size-1000', '1fr')];

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
                    gap={'var(--gap)'}
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
                            <ActionElement UNSAFE_className={classes.itemMediaName}>{name}</ActionElement>
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
