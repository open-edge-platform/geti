// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@geti/ui';

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
