// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Flex, Text, View } from '@adobe/react-spectrum';

import { useReconfigAutoTraining } from '../../../../../core/configurable-parameters/hooks/use-reconfig-auto-training.hook';
import { findRequiredImagesAutoTrainingConfig } from '../../../../../core/configurable-parameters/utils';
import { Task } from '../../../../../core/projects/task.interface';
import {
    ConfigurableParametersTaskChain,
    NumberGroupParams,
} from '../../../configurable-parameters/configurable-parameters.interface';
import { Slider } from '../../../slider/slider.component';

interface RequiredAnnotationsSliderProps {
    task: Task;
    requiredImagesAutoTrainingConfig: NumberGroupParams;
    autoTrainingOptimisticUpdates: ReturnType<typeof useReconfigAutoTraining>;
    configParameters: ConfigurableParametersTaskChain[];
}

export const RequiredAnnotationsSlider: FC<RequiredAnnotationsSliderProps> = ({
    task,
    requiredImagesAutoTrainingConfig,
    autoTrainingOptimisticUpdates,
    configParameters,
}) => {
    const [numberOfRequiredAnnotations, setNumberOfRequiredAnnotations] = useState<number>(
        requiredImagesAutoTrainingConfig.value
    );

    const handleRequiredAnnotationsChange = (newNumberOfRequiredAnnotations: number) => {
        autoTrainingOptimisticUpdates.mutate({
            configParameters,
            newConfigParameter: {
                ...requiredImagesAutoTrainingConfig,
                value: newNumberOfRequiredAnnotations,
            },
            onOptimisticUpdate: (config) => {
                const requiredImagesAutoTrainingConfigOptimistic = findRequiredImagesAutoTrainingConfig(
                    task.id,
                    config
                );

                if (requiredImagesAutoTrainingConfigOptimistic !== undefined) {
                    requiredImagesAutoTrainingConfigOptimistic.value = newNumberOfRequiredAnnotations;
                }

                return config;
            },
        });
    };

    return (
        <Flex alignItems={'center'} gap={'size-100'}>
            <Slider
                step={1}
                value={numberOfRequiredAnnotations}
                minValue={requiredImagesAutoTrainingConfig.minValue}
                maxValue={requiredImagesAutoTrainingConfig.maxValue}
                onChange={setNumberOfRequiredAnnotations}
                onChangeEnd={handleRequiredAnnotationsChange}
                label={'Number of required annotations'}
                getValueLabel={() => ''}
                isFilled
            />

            <View
                backgroundColor={'gray-50'}
                padding={'size-100'}
                borderColor={'gray-400'}
                borderRadius={'small'}
                borderWidth={'thin'}
                marginTop={'size-115'}
            >
                <Text>{numberOfRequiredAnnotations}</Text>
            </View>
        </Flex>
    );
};
