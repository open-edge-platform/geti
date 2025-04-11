// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Text, View } from '@adobe/react-spectrum';

import { Switch } from '../../../../switch/switch.component';
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
