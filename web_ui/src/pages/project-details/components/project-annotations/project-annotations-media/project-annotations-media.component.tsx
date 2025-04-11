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
import CountUp from 'react-countup';

import { CardContent } from '../../../../../shared/components/card-content/card-content.component';
import { ProjectGridArea } from '../project-grid-area.interface';

import classes from './project-annotations-media.module.scss';

interface ProjectAnnotationsMediaProps extends ProjectGridArea {
    images: number;
    videos: number;
}

export const ProjectAnnotationsMedia = ({ gridArea, images, videos }: ProjectAnnotationsMediaProps): JSX.Element => {
    return (
        <CardContent title='Number of media' gridArea={gridArea}>
            <Flex justifyContent='space-around' alignItems='center' height='100%'>
                <Flex direction='column' alignItems={'center'} justifyContent={'center'}>
                    <Text
                        UNSAFE_className={classes.projectAnnotationsMediaLargeText}
                        data-testid='media-images-count-id'
                        id='media-images-count-id'
                    >
                        <CountUp end={images} />
                    </Text>
                    <Text
                        UNSAFE_className={classes.projectAnnotationsMediaSmallText}
                        data-testid='media-images-id'
                        id='media-images-id'
                    >
                        Images
                    </Text>
                </Flex>
                <Flex direction='column' alignItems={'center'} justifyContent={'center'}>
                    <Text
                        UNSAFE_className={classes.projectAnnotationsMediaLargeText}
                        data-testid='media-videos-count-id'
                        id='media-videos-count-id'
                    >
                        <CountUp end={videos} />
                    </Text>
                    <Text
                        UNSAFE_className={classes.projectAnnotationsMediaSmallText}
                        data-testid='media-videos-id'
                        id='media-videos-id'
                    >
                        Videos
                    </Text>
                </Flex>
            </Flex>
        </CardContent>
    );
};
