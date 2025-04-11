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

import { useEffect, useRef } from 'react';

import { TextFieldRef } from '@react-types/textfield';
import noop from 'lodash/noop';

import { LabelItemEditionState } from '../../../../../../core/labels/label-tree-view.interface';
import { LimitedTextField } from '../../../../limited-text-field/limited-text-field.component';

interface NameEditionFieldProps {
    value: string | undefined;
    onChange: (value: string) => void;
    error: string;
    labelState: LabelItemEditionState;
    gridArea?: string;
    onFocusChange?: (isFocused: boolean) => void;
}

export const NameEditionField = ({
    onChange,
    error,
    value,
    gridArea,
    labelState,
    onFocusChange = noop,
}: NameEditionFieldProps): JSX.Element => {
    const newChildNameRef = useRef<TextFieldRef>(null);

    useEffect(() => {
        labelState === LabelItemEditionState.NEW_DEFAULT && newChildNameRef.current && newChildNameRef.current.select();
    }, [labelState]);

    return (
        <LimitedTextField
            minWidth={0}
            width={'100%'}
            value={value}
            onFocusChange={onFocusChange}
            ref={newChildNameRef}
            onChange={onChange}
            validationState={error ? 'invalid' : undefined}
            aria-label={'edited name'}
            data-testid={`label-tree-${value}-name-input`}
            id={`label-tree-${value}-${value}`}
            gridArea={gridArea}
        />
    );
};
