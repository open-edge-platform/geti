// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Switch, Text, View } from '@geti/ui';

import { BooleanGroupParams } from '../../../configurable-parameters.interface';
import { ResetButtonHandler } from '../cp-editable-item.interface';

interface CPBooleanProps extends ResetButtonHandler {
    parameter: BooleanGroupParams;
}

export const CPBoolean = ({ id, parameter, updateParameter }: CPBooleanProps): JSX.Element => {
    const { id: parameterId, value } = parameter;

    const handleSelectChange = (isSelected: boolean): void => {
        updateParameter && updateParameter(parameterId, isSelected);
    };

    return (
        <View>
            <Switch
                id={`${id}-boolean-field-id`}
                aria-label={parameter.name}
                onChange={handleSelectChange}
                isSelected={value}
            >
                <Text id={`${id}-content-id`}>{value ? 'On' : 'Off'}</Text>
            </Switch>
        </View>
    );
};
