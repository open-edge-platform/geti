// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { ActionButton, Flex, Grid, minmax, Text, View } from '@geti/ui';
import { Refresh } from '@geti/ui/icons';

import {
    ConfigurationParameter,
    NumberParameter,
    TrainingConfiguration,
} from '../../../../../../../../core/configurable-parameters/services/configuration.interface';
import { Accordion } from '../../ui/accordion/accordion.component';
import { SubsetsDistributionSlider } from './subsets-distribution-slider/subsets-distribution-slider.component';

import styles from './training-subsets.module.scss';

interface SubsetDistributionStatsProps {
    trainingCount: number;
    validationCount: number;
    testCount: number;
}

const Tile: FC<{ color: string }> = ({ color }) => {
    return (
        <View height={'size-100'} width={'size-100'} borderRadius={'small'} UNSAFE_style={{ backgroundColor: color }} />
    );
};

const SubsetDistributionStat: FC<{ count: number; color: string; title: string }> = ({ count, color, title }) => {
    return (
        <Flex alignItems={'center'} gap={'size-50'}>
            <Tile color={color} />
            <Text>
                {title}: {count}
            </Text>
        </Flex>
    );
};

const SubsetDistributionStats: FC<SubsetDistributionStatsProps> = ({ trainingCount, validationCount, testCount }) => {
    return (
        <View gridArea={'counts'} backgroundColor={'static-gray-800'} borderRadius={'small'} padding={'size-100'}>
            <Flex alignItems={'center'} justifyContent={'space-between'} UNSAFE_className={styles.statsText}>
                <Flex alignItems={'center'} gap={'size-200'}>
                    <SubsetDistributionStat title={'Training'} color={'var(--training-subset)'} count={trainingCount} />
                    <SubsetDistributionStat
                        title={'Validation'}
                        color={'var(--validation-subset)'}
                        count={validationCount}
                    />
                    <SubsetDistributionStat title={'Test'} color={'var(--test-subset)'} count={testCount} />
                </Flex>
                <Text>
                    <Text UNSAFE_className={styles.totalStats}>Total: </Text>
                    {trainingCount + validationCount + testCount} media items
                </Text>
            </Flex>
        </View>
    );
};

interface SubsetsDistributionProps {
    trainingSubsetCount: number;
    validationSubsetCount: number;
    testSubsetCount: number;
    subsetsDistribution: number[];
    onSubsetsDistributionChange: (values: number[]) => void;
    onSubsetsDistributionChangeEnd: (values: number[]) => void;
    onSubsetsDistributionReset: () => void;
}

const SubsetsDistribution: FC<SubsetsDistributionProps> = ({
    subsetsDistribution,
    trainingSubsetCount,
    testSubsetCount,
    validationSubsetCount,
    onSubsetsDistributionChange,
    onSubsetsDistributionChangeEnd,
    onSubsetsDistributionReset,
}) => {
    const handleSubsetDistributionChange = (values: number[] | number): void => {
        if (Array.isArray(values)) {
            onSubsetsDistributionChange(values);
        }
    };

    const handleSubsetDistributionChangeEnd = (values: number[] | number): void => {
        if (Array.isArray(values)) {
            onSubsetsDistributionChangeEnd(values);
        }
    };

    return (
        <View UNSAFE_className={styles.trainingSubsets}>
            <Grid
                areas={['label slider reset', '. counts .']}
                columns={['max-content', minmax('size-3400', '1fr'), 'max-content']}
                alignItems={'center'}
                columnGap={'size-250'}
            >
                <SubsetsDistributionSlider
                    aria-label={'Distribute samples'}
                    minValue={0}
                    maxValue={100}
                    step={1}
                    value={[subsetsDistribution[0], subsetsDistribution[1]]}
                    onChange={handleSubsetDistributionChange}
                    onChangeEnd={handleSubsetDistributionChangeEnd}
                    label={'Distribution'}
                />
                <ActionButton isQuiet gridArea={'reset'} onPress={onSubsetsDistributionReset}>
                    <Refresh />
                </ActionButton>
                <SubsetDistributionStats
                    testCount={testSubsetCount}
                    trainingCount={trainingSubsetCount}
                    validationCount={validationSubsetCount}
                />
            </Grid>
        </View>
    );
};

const MAX_RATIO_VALUE = 100;

type SubsetsConfiguration = TrainingConfiguration['datasetPreparation']['subsetSplit'];

interface TrainingSubsetsProps {
    subsetsConfiguration: SubsetsConfiguration;
    onUpdateTrainingConfiguration: (
        updateFunction: (config: TrainingConfiguration | undefined) => TrainingConfiguration | undefined
    ) => void;
}

const TEST_SUBSET_KEY = 'test';
const VALIDATION_SUBSET_KEY = 'validation';
const TRAINING_SUBSET_KEY = 'training';

const getSubsets = (subsetsConfiguration: SubsetsConfiguration) => {
    const testSubset = subsetsConfiguration.find((parameter) => parameter.key === TEST_SUBSET_KEY) as NumberParameter;
    const validationSubset = subsetsConfiguration.find(
        (parameter) => parameter.key === VALIDATION_SUBSET_KEY
    ) as NumberParameter;
    const trainingSubset = subsetsConfiguration.find(
        (parameter) => parameter.key === TRAINING_SUBSET_KEY
    ) as NumberParameter;

    return {
        trainingSubset,
        validationSubset,
        testSubset,
    };
};

export const TrainingSubsets: FC<TrainingSubsetsProps> = ({ subsetsConfiguration, onUpdateTrainingConfiguration }) => {
    const { trainingSubset, validationSubset, testSubset } = getSubsets(subsetsConfiguration);

    const [subsetsDistribution, setSubsetsDistribution] = useState<number[]>([
        trainingSubset.value,
        trainingSubset.value + validationSubset.value,
    ]);

    const trainingSubsetRatio = subsetsDistribution[0];
    const validationSubsetRatio = subsetsDistribution[1] - trainingSubsetRatio;
    const testSubsetRatio = MAX_RATIO_VALUE - subsetsDistribution[1];

    const handleUpdateSubsetsConfiguration = (values: number[]): void => {
        onUpdateTrainingConfiguration((config) => {
            if (!config) return undefined;

            const newConfig = structuredClone(config);
            const trainingSubsetValue = values[0];
            const validationSubsetValue = values[1] - trainingSubsetValue;
            const testSubsetValue = MAX_RATIO_VALUE - values[1];

            const KEY_VALUE_MAP = {
                [TRAINING_SUBSET_KEY]: trainingSubsetValue,
                [VALIDATION_SUBSET_KEY]: validationSubsetValue,
                [TEST_SUBSET_KEY]: testSubsetValue,
            };

            newConfig.datasetPreparation.subsetSplit = config.datasetPreparation.subsetSplit.map((parameter) => {
                if (
                    TRAINING_SUBSET_KEY === parameter.key ||
                    VALIDATION_SUBSET_KEY === parameter.key ||
                    TEST_SUBSET_KEY === parameter.key
                ) {
                    return {
                        ...parameter,
                        value: KEY_VALUE_MAP[parameter.key],
                    } as ConfigurationParameter;
                }
                return parameter;
            });

            return newConfig;
        });
    };

    const handleSubsetsConfigurationReset = (): void => {
        setSubsetsDistribution([
            trainingSubset.defaultValue,
            trainingSubset.defaultValue + validationSubset.defaultValue,
        ]);

        onUpdateTrainingConfiguration((config) => {
            if (config === undefined) return undefined;

            const newConfig = structuredClone(config);

            newConfig.datasetPreparation.subsetSplit = config.datasetPreparation.subsetSplit.map((parameter) => {
                if ([VALIDATION_SUBSET_KEY, TEST_SUBSET_KEY, TRAINING_SUBSET_KEY].includes(parameter.key)) {
                    return {
                        ...parameter,
                        value: parameter.defaultValue,
                    } as ConfigurationParameter;
                }

                return parameter;
            });

            return newConfig;
        });
    };

    return (
        <Accordion>
            <Accordion.Title>
                Training subsets
                <Accordion.Tag>
                    {trainingSubsetRatio}/{validationSubsetRatio}/{testSubsetRatio}%
                </Accordion.Tag>
            </Accordion.Title>
            <Accordion.Content>
                <Accordion.Description>
                    Specify the distribution of annotated samples over the training, validation and test subsets. Note:
                    items that have already been used for training will stay in the same subset even if these parameters
                    are changed.
                </Accordion.Description>
                <Accordion.Divider marginY={'size-250'} />
                <SubsetsDistribution
                    subsetsDistribution={subsetsDistribution}
                    onSubsetsDistributionChange={setSubsetsDistribution}
                    testSubsetCount={testSubset.value}
                    trainingSubsetCount={trainingSubset.value}
                    validationSubsetCount={validationSubset.value}
                    onSubsetsDistributionChangeEnd={handleUpdateSubsetsConfiguration}
                    onSubsetsDistributionReset={handleSubsetsConfigurationReset}
                />
            </Accordion.Content>
        </Accordion>
    );
};
