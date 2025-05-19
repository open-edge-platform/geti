// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode } from 'react';

import { Grid, minmax, Text, View } from '@geti/ui';
import { isFunction } from 'lodash-es';

import { ConfigurableParametersParams } from '../../../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { BooleanParameter } from './boolean-parameter.component';
import { NumberParameter } from './number-parameter.component';
import { ResetButton } from './reset-button.component';
import { ToggleButtons } from './toggle-buttons/toggle-buttons.component';
import { Tooltip } from './tooltip.component';

interface ParametersProps {
    parameters: ConfigurableParametersParams[];
    onChange: () => void;
}

const ParameterTooltip: FC<{ text: string }> = ({ text }) => {
    return <Tooltip>{text}</Tooltip>;
};

interface ParameterProps {
    parameter: ConfigurableParametersParams;
    onChange: () => void;
}

interface ParameterLayoutProps {
    header: string;
    description: string;
    onReset: () => void;
    children: ReactNode;
}

const ParameterLayout: FC<ParameterLayoutProps> = ({ header, children, description, onReset }) => {
    return (
        <>
            <Text gridColumn={'1/2'}>
                {header}
                <ParameterTooltip text={description} />
            </Text>
            <View gridColumn={'2/3'}>{children}</View>
            {isFunction(onReset) && <ResetButton onPress={onReset} aria-label={`Reset ${header}`} />}
        </>
    );
};

const ParameterField: FC<ParameterProps> = ({ parameter, onChange }) => {
    if (parameter.dataType === 'string' && parameter.templateType === 'selectable') {
        return <ToggleButtons options={parameter.options} selectedOption={parameter.value} onOptionChange={onChange} />;
    }

    if (parameter.templateType === 'input' && (parameter.dataType === 'float' || parameter.dataType === 'integer')) {
        return (
            <NumberParameter
                value={parameter.value}
                minValue={parameter.minValue}
                maxValue={parameter.maxValue}
                onChange={onChange}
                type={parameter.dataType}
            />
        );
    }

    if (parameter.dataType === 'boolean') {
        return <BooleanParameter value={parameter.value} header={parameter.header} onChange={() => {}} />;
    }
};

const Parameter: FC<ParameterProps> = ({ parameter, onChange }) => {
    return (
        <ParameterLayout header={parameter.header} description={parameter.description} onReset={() => {}}>
            <ParameterField parameter={parameter} onChange={onChange} />
        </ParameterLayout>
    );
};

export const Parameters: FC<ParametersProps> = ({ parameters, onChange }) => {
    return (
        <Grid columns={['size-3000', minmax('size-3400', '1fr'), 'size-400']} gap={'size-300'} alignItems={'center'}>
            {parameters.map((parameter) => (
                <Parameter key={parameter.name} parameter={parameter} onChange={onChange} />
            ))}
        </Grid>
    );
};
