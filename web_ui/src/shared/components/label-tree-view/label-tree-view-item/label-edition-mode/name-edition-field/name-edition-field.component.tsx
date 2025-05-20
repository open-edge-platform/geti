// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { TextFieldRef } from '@geti/ui';
import { noop } from 'lodash-es';

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
