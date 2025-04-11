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

import { Flex, Text } from '@adobe/react-spectrum';
import CountUp from 'react-countup';

import { CardContent } from '../../../../../shared/components/card-content/card-content.component';
import { ProjectGridArea } from '../project-grid-area.interface';

import classes from './project-annotations-videos.module.scss';

interface ProjectAnnotationsVideosProps extends ProjectGridArea {
    annotatedVideos: number;
    annotatedFrames: number;
}

export const ProjectAnnotationsVideos = ({
    annotatedFrames,
    annotatedVideos,
    gridArea,
}: ProjectAnnotationsVideosProps): JSX.Element => {
    return (
        <CardContent title='Annotated videos / frames' gridArea={gridArea}>
            <Flex direction={'column'} justifyContent={'center'} height={'100%'} marginStart={'size-130'}>
                <Flex alignItems={'center'} gap={'size-200'}>
                    <Text id='annotated-videos-id'>Videos:</Text>
                    <Text
                        UNSAFE_className={classes.projectAnnotationsVideosText}
                        data-testid='annotated-videos-count-id'
                        id='annotated-videos-count-id'
                    >
                        <CountUp end={annotatedVideos} />
                    </Text>
                </Flex>
                <Flex alignItems={'center'} gap={'size-200'}>
                    <Text id='annotated-frames-id'>Frames:</Text>
                    <Text
                        UNSAFE_className={classes.projectAnnotationsVideosText}
                        data-testid='annotated-frame-count-id'
                        id='annotated-frame-count-id'
                    >
                        <CountUp end={annotatedFrames} />
                    </Text>
                </Flex>
            </Flex>
        </CardContent>
    );
};
