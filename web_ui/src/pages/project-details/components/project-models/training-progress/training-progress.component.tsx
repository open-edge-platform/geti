// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Heading, Text, View } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';
import { JobsListItemStatus } from '../../../../../shared/components/header/jobs-management/jobs-list-item-status.component';
import { TrainingModelCard } from '../models-container/training-model-card/training-model-card.component';
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
                            {trainingData.trainingDetails.length > 1 ? 'Current jobs' : 'Current job'}
                        </Text>
                        {trainingData.trainingDetails.map((job) => (
                            <View
                                borderTopStartRadius={'small'}
                                borderTopEndRadius={'small'}
                                backgroundColor={'gray-75'}
                                marginTop={'size-100'}
                            >
                                <Heading
                                    id={`model-group-name-${job.id}-id`}
                                    margin={0}
                                    UNSAFE_style={{ padding: '16px' }}
                                >
                                    {job.metadata.task.modelArchitecture}
                                </Heading>
                                <Divider size='S' />
                                <TrainingModelCard job={job} />
                                <JobsListItemStatus expanded={false} job={job} />
                            </View>
                        ))}
                    </View>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
