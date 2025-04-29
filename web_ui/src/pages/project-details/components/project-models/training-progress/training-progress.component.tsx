// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Text, View } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';
import { JobsListItemStatus } from '../../../../../shared/components/header/jobs-management/jobs-list-item-status.component';
import { formatJobsCreationTime } from '../../../../../shared/utils';
import { TrainingProgressTask } from './training-progress-task/training-progress-task.component';
import { useTrainingProgress } from './use-training-progress/use-training-progress.hook';

interface TrainingProgressProps {
    taskId: string;
}

export const TrainingProgress = ({ taskId }: TrainingProgressProps): JSX.Element => {
    const trainingData = useTrainingProgress(taskId);

    return (
        <AnimatePresence mode='wait'>
            {trainingData.showTrainingProgress && (
                <motion.div
                    variants={ANIMATION_PARAMETERS.ANIMATE_ELEMENT_WITH_JUMP}
                    initial={'hidden'}
                    animate={'visible'}
                    exit={'exit'}
                >
                    <View marginTop={'size-100'} marginBottom={'size-200'}>
                        <Text id={`current-training-${taskId}-id`} data-testid={`current-training-${taskId}-id`}>
                            Current job
                        </Text>
                        <View
                            borderTopStartRadius={'small'}
                            borderTopEndRadius={'small'}
                            backgroundColor={'gray-75'}
                            marginTop={'size-100'}
                        >
                            <View paddingTop={'size-250'} paddingX={'size-200'}>
                                <TrainingProgressTask
                                    name={trainingData.trainingDetails.metadata.task.name?.split(' task')[0] ?? ''}
                                    architecture={trainingData.trainingDetails.metadata.task.modelArchitecture ?? ''}
                                    creationTime={formatJobsCreationTime(trainingData.trainingDetails.creationTime)}
                                />
                                <Divider size={'S'} marginY={'size-200'} />
                            </View>
                            <JobsListItemStatus expanded={false} job={trainingData.trainingDetails} />
                        </View>
                    </View>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
