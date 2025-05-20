// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Flex, Grid, View } from '@geti/ui';

import { filterOutEmptyLabel } from '../../../../../core/labels/utils';
import { isKeypointTask } from '../../../../../core/projects/utils';
import { trimText } from '../../../../../shared/utils';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { VideoTimeline } from './video-timeline.component';

import classes from './video-annotator.module.scss';

interface VideoAnnotatorProps {
    selectFrame: (frameNumber: number) => void;
}
const MAX_LABEL_LENGTH = 32;

const useTaskLabels = () => {
    const { labels, tasks } = useTask();

    return useMemo(() => {
        const filteredLabels = filterOutEmptyLabel(labels);

        if (tasks.some(isKeypointTask)) {
            return [{ ...filteredLabels[0], name: 'Keypoint', color: 'var(--energy-blue)' }];
        }

        return filteredLabels;
    }, [tasks, labels]);
};

export const VideoAnnotator = ({ selectFrame }: VideoAnnotatorProps): JSX.Element => {
    const labels = useTaskLabels();

    return (
        <Grid
            areas={['. timeline', 'labels timeline']}
            columns={['size-2000', 'auto']}
            rows={['size-500', 'auto']}
            maxHeight='size-2000'
            UNSAFE_style={{ overflowY: 'auto' }}
        >
            <View
                top={0}
                left={0}
                width='size-2000'
                height='100%'
                gridArea='labels'
                position='sticky'
                backgroundColor='gray-100'
            >
                <Flex direction='column' gap='size-100'>
                    {labels.map((label) => (
                        <View
                            key={`label-${label.id}`}
                            height='size-225'
                            paddingX='size-50'
                            backgroundColor='gray-200'
                            UNSAFE_className={classes.groupedLabels}
                        >
                            <Flex data-testid={`video-labels-${label.id}`} alignItems={'center'} height={'100%'}>
                                {trimText(label.name, MAX_LABEL_LENGTH)}
                            </Flex>
                        </View>
                    ))}
                </Flex>
            </View>

            <VideoTimeline selectFrame={selectFrame} labels={labels} />
        </Grid>
    );
};
