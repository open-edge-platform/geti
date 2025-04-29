// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CPBoolean } from './cp-boolean/cp-boolean.component';
import { CPEditableItemProps } from './cp-editable-item.interface';
import { CPNumber } from './cp-number/cp-number.component';
import { CPSelectableList } from './cp-selectable/cp-selectable-list.component';

export const CPEditableItem = ({ id, parameter, updateParameter }: CPEditableItemProps): JSX.Element => {
    if (parameter.dataType === 'boolean') {
        return <CPBoolean id={id} parameter={parameter} updateParameter={updateParameter} />;
    } else if (parameter.templateType === 'input') {
        return <CPNumber id={id} parameter={parameter} updateParameter={updateParameter} />;
    } else if (parameter.templateType === 'selectable') {
        if (parameter.dataType === 'string') {
            return <CPSelectableList id={id} parameter={parameter} updateParameter={updateParameter} />;
        }

        return <CPSelectableList id={id} parameter={parameter} updateParameter={updateParameter} />;
    }

    throw new Error('That parameter is not supported');
};
