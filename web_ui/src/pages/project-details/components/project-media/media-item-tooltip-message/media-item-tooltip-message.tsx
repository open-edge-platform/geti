// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';

import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { useUsers } from '../../../../../core/users/hook/use-users.hook';
import { useOrganizationIdentifier } from '../../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { FullnameWithLoading } from '../../../../../shared/components/users/fullname.component';
import { formatDate, isNonEmptyString } from '../../../../../shared/utils';

interface MediaItemTooltipMessageBaseProps {
    id: string;
    fileName: string;
    fileSize: string;
    type: MEDIA_TYPE;
    uploadTime: string;
    uploaderId: string;
    resolution: string;
    lastAnnotatorId: string | null;
}

interface MediaItemTooltipMessageImageProps extends MediaItemTooltipMessageBaseProps {
    type: MEDIA_TYPE.IMAGE;
    resolution: string;
}

interface MediaItemTooltipMessageVideoProps extends MediaItemTooltipMessageBaseProps {
    type: MEDIA_TYPE.VIDEO;
    fps: number;
    duration: number;
}

interface MediaItemTooltipMessageVideoFrameProps extends MediaItemTooltipMessageBaseProps {
    type: MEDIA_TYPE.VIDEO_FRAME;
}

export type MediaItemTooltipMessageProps =
    | MediaItemTooltipMessageImageProps
    | MediaItemTooltipMessageVideoProps
    | MediaItemTooltipMessageVideoFrameProps;

export const MediaItemTooltipMessage = (props: MediaItemTooltipMessageProps): JSX.Element => {
    const { fileName, uploaderId, uploadTime, id, type, fileSize, lastAnnotatorId } = props;

    const { organizationId } = useOrganizationIdentifier();
    const { useGetUserQuery } = useUsers();
    const lastAnnotatorQuery = useGetUserQuery(organizationId, lastAnnotatorId ?? undefined);
    const uploaderQuery = useGetUserQuery(organizationId, uploaderId);

    return (
        <Flex direction={'column'} id={`media-item-tooltip-${id}`}>
            <Text id={`${id}-filename-id`}>File name: {fileName}</Text>
            {isNonEmptyString(fileSize) && <Text id={`${id}-filesize-id`}>Size: {fileSize}</Text>}
            <Text id={`${id}-resolution-id`}>Resolution: {props.resolution}</Text>
            {type === MEDIA_TYPE.VIDEO && (
                <>
                    <Text id={`${id}-fps-id`}>FPS: {props.fps.toFixed(2)}</Text>
                    <Text id={`${id}-time-id`}>Duration: {props.duration}s</Text>
                </>
            )}
            <Text id={`${id}-upload-time-id`}>Upload time: {formatDate(uploadTime, 'DD MMM YYYY HH:mm:ss')}</Text>
            <Text id={`${id}-owner-id`}>
                Owner: <FullnameWithLoading user={uploaderQuery.data} isLoading={uploaderQuery.isInitialLoading} />
            </Text>
            {lastAnnotatorId && (
                <Text id={`${id}-last-editor-id`}>
                    Last annotator:{' '}
                    <FullnameWithLoading
                        user={lastAnnotatorQuery.data}
                        isLoading={lastAnnotatorQuery.isInitialLoading}
                    />
                </Text>
            )}
        </Flex>
    );
};
