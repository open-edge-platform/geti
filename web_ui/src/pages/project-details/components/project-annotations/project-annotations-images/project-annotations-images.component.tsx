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
