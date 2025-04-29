// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Content, ContextualHelp, Text } from '@adobe/react-spectrum';

import { NumberGroupParams } from '../../../../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { NumberParameter } from '../../ui/number-parameter.component';
import { ResetButton } from '../../ui/reset-button.component';

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

    const handleResetToDefault = () => {
        setParameterValue(defaultValue);
    };

    return (
        <>
            <Text gridColumn={'1/2'}>
                {header}
                <TilingManualModeOptionTooltip text={description} />
            </Text>
            <NumberParameter
                value={parameterValue}
                minValue={minValue}
                maxValue={maxValue}
                onChange={setParameterValue}
                type={parameter.dataType}
            />
            <ResetButton aria-label={`Reset ${header}`} gridColumn={'3/4'} onPress={handleResetToDefault} />
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
