// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Heading, Text, View } from '@adobe/react-spectrum';

import { JobState } from '../../../../../../core/jobs/jobs.const';
import { useModels } from '../../../../../../core/models/hooks/use-models.hook';
import { ThreeDotsFlashing } from '../../../../../../shared/components/three-dots-flashing/three-dots-flashing.component';
import { formatDate } from '../../../../../../shared/utils';
import { TrainingModelCardProps } from '../model-card/model-card.interface';
import { ModelInfoFields } from '../model-card/model-info-fields.component';
import { ModelPerformance } from '../model-card/model-performance.component';

import classes from '../model-card/model-card.module.scss';

export const TrainingModelCard = ({ job }: TrainingModelCardProps) => {
    const { useProjectModelsQuery } = useModels();
    const { data: modelsData = [] } = useProjectModelsQuery();

    const trainedModel = modelsData.find((model) =>
        model.modelVersions.find((modelVersion) => modelVersion.groupName == job.metadata.task.modelArchitecture)
    );
    const genericId = `training-model-${job.metadata.trainedModel.modelId}`;
    // incrementing model version by 1 to show the next version that will be created after training
    const modelVersion = (trainedModel?.modelVersions[0].version ?? 0) + 1;

    return (
        <div
            className={classes.modelCard}
            aria-label={`${job.metadata.task.modelArchitecture} version ${modelVersion}`}
        >
            <View
                borderWidth={'thin'}
                borderRadius={'small'}
                borderColor={'gray-75'}
                UNSAFE_className={classes.modelCardTraining}
            >
                <Flex alignItems={'center'} gap={'size-200'}>
                    <ModelPerformance
                        genericId={genericId}
                        performance={undefined}
                        isDisabled={false}
                        isModelTraining={true}
                    />
                    <Flex direction={'column'} width={'100%'} gap='size-100'>
                        <Flex alignItems={'center'} justifyContent={'space-between'}>
                            <Text UNSAFE_className={classes.modelInfo} data-testid={'trained-model-date-id'}>
                                Trained: {formatDate(job.creationTime, 'DD MMM YYYY, hh:mm A')}
                            </Text>
                        </Flex>
                        <Flex alignItems={'center'} gap='size-150'>
                            {job.state === JobState.RUNNING ? (
                                <Heading
                                    id={`version-${genericId}-id`}
                                    data-testid={`version-${genericId}-id`}
                                    margin={0}
                                >
                                    Version {modelVersion}
                                </Heading>
                            ) : (
                                <>
                                    <Heading
                                        id={`version-${genericId}-id`}
                                        data-testid={`version-${genericId}-id`}
                                        margin={0}
                                    >
                                        Version
                                    </Heading>
                                    <ThreeDotsFlashing className={classes.modelVersionThreeDotsFlashing} />
                                </>
                            )}
                        </Flex>
                        <Text
                            id={`model-info-${genericId}-id`}
                            data-testid={`model-info-${genericId}-id`}
                            UNSAFE_className={classes.modelInfo}
                        >
                            <ModelInfoFields isModelTraining={true} />
                        </Text>
                    </Flex>
                </Flex>
            </View>
        </div>
    );
};
