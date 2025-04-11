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
