// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Flex, Slider, Text, View } from '@geti/ui';

import { NumberGroupParams } from '../../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { NumberParameter } from '../../../../../core/configurable-parameters/services/configuration.interface';

interface RequiredAnnotationsSliderProps {
    requiredImagesAutoTrainingConfig: NumberGroupParams | NumberParameter;
    onUpdateRequiredAnnotations: (newNumberOfRequiredAnnotations: number) => void;
}

export const RequiredAnnotationsSlider: FC<RequiredAnnotationsSliderProps> = ({
    requiredImagesAutoTrainingConfig,
    onUpdateRequiredAnnotations,
}) => {
    const [numberOfRequiredAnnotations, setNumberOfRequiredAnnotations] = useState<number>(
        requiredImagesAutoTrainingConfig.value
    );

    return (
        <Flex alignItems={'center'} gap={'size-100'}>
            <Slider
                step={1}
                value={numberOfRequiredAnnotations}
                minValue={requiredImagesAutoTrainingConfig.minValue}
                maxValue={requiredImagesAutoTrainingConfig.maxValue}
                onChange={setNumberOfRequiredAnnotations}
                onChangeEnd={onUpdateRequiredAnnotations}
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
