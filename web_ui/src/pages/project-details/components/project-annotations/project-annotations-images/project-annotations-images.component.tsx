// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@geti/ui';
import CountUp from 'react-countup';

import { CardContent } from '../../../../../shared/components/card-content/card-content.component';
import { ProgressBar } from '../../../../../shared/components/progress-bar/progress-bar.component';
import { ProjectGridArea } from '../project-grid-area.interface';

import classes from './project-annotations-images.module.scss';

interface ProjectAnnotationsImagesProps extends ProjectGridArea {
    annotatedImages: number;
    images: number;
}

export const ProjectAnnotationsImages = ({
    annotatedImages,
    images,
    gridArea,
}: ProjectAnnotationsImagesProps): JSX.Element => {
    return (
        <CardContent title='Annotated images' gridArea={gridArea}>
            <Flex direction={'column'} alignItems={'center'} justifyContent={'center'} height={'100%'}>
                <Text
                    UNSAFE_className={classes.projectAnnotationsImagesText}
                    data-testid='annotated-images-count-id'
                    id='annotated-images-count-id'
                >
                    <CountUp end={annotatedImages} />
                </Text>
                <ProgressBar
                    value={Math.round((annotatedImages / images) * 100) || 0}
                    UNSAFE_className={classes.projectAnnotationsImagesProgressBar}
                    labelPosition={'side'}
                    aria-label={'Annotated images'}
                    showValueLabel
                    id='annotated-images-progress-bar-id'
                />
            </Flex>
        </CardContent>
    );
};
