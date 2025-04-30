// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Content, ContextualHelp, Flex, NumberField, Text } from '@adobe/react-spectrum';

import { Refresh } from '../../../../../../../../assets/icons';
import { ActionButton } from '../../../../../../../../shared/components/button/button.component';
import { NumberGroupParams } from '../../../../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { Slider } from '../../../../../../../../shared/components/slider/slider.component';
import { getFloatingPointStep } from '../../utils';

const TilingManualModeOptionTooltip: FC<{ text: string }> = ({ text }) => {
    return (
        <ContextualHelp variant='info'>
            <Content>
                <Text>{text}</Text>
            </Content>
        </ContextualHelp>
    );
};

const TilingOption: FC<{ parameter: NumberGroupParams }> = ({ parameter }) => {
    const { description, header, minValue, maxValue, value, defaultValue } = parameter;

    const [parameterValue, setParameterValue] = useState<number>(value);

    const floatingPointStep = getFloatingPointStep(minValue, maxValue);

    const step = parameter.dataType === 'integer' ? 1 : floatingPointStep;

    const handleResetToDefault = () => {
        setParameterValue(defaultValue);
    };

    return (
        <>
            <Text gridColumn={'1/2'}>
                {header}
                <TilingManualModeOptionTooltip text={description} />
            </Text>
            <Flex gap={'size-100'}>
                <Slider
                    defaultValue={defaultValue}
                    value={parameterValue}
                    minValue={minValue}
                    maxValue={maxValue}
                    onChange={setParameterValue}
                    step={step}
                    isFilled
                />
                <NumberField
                    isQuiet
                    step={step}
                    defaultValue={defaultValue}
                    value={parameterValue}
                    minValue={minValue}
                    maxValue={maxValue}
                    onChange={setParameterValue}
                />
            </Flex>
            <ActionButton isQuiet aria-label={`Reset ${header}`} gridColumn={'3/4'} onPress={handleResetToDefault}>
                <Refresh />
            </ActionButton>
        </>
    );
};

interface TilingOptions {
    parameters: NumberGroupParams[];
}

export const TilingOptions: FC<TilingOptions> = ({ parameters }) => {
    return (
        <>
            {parameters.map((parameter) => (
                <TilingOption parameter={parameter} key={parameter.id} />
            ))}
        </>
    );
};
