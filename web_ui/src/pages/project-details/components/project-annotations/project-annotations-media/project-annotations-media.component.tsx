// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
