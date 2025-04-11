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

import { Flex } from '@adobe/react-spectrum';

import { ConfigGroupParametersDataTypesDTO } from '../../../../../../core/configurable-parameters/dtos/configurable-parameters.interface';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';
import { SelectableGroupParams } from '../../../configurable-parameters.interface';
import { ResetButtonHandler } from '../cp-editable-item.interface';
import { CPSelectableItem } from './cp-selectable-item.component';

interface CPSelectableProps<T extends string | number> extends ResetButtonHandler {
    parameter: SelectableGroupParams<T, ConfigGroupParametersDataTypesDTO>;
}

export const CPSelectableList = <T extends string | number>(props: CPSelectableProps<T>): JSX.Element => {
    const { id, parameter, updateParameter } = props;
    const { value, options, id: parameterId } = parameter;

    const handleOptionChange = (selectedOptionItem: T): void => {
        updateParameter && updateParameter(parameterId, selectedOptionItem);
    };

    return (
        <Flex gap={'size-125'}>
            {options.map((option) => (
                <CPSelectableItem
                    id={`${id}-${idMatchingFormat(option)}-id`}
                    key={option}
                    value={option}
                    selectedOption={value}
                    handleOptionChange={handleOptionChange}
                />
            ))}
        </Flex>
    );
};
