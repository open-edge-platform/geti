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

import isFunction from 'lodash/isFunction';

import { Label } from '../../../../../../core/labels/label.interface';
import { LabelColorThumb } from '../../../../../../shared/components/label-color-thumb/label-color-thumb.component';
import { TruncatedText } from '../../../../../../shared/components/truncated-text/truncated-text.component';
import { LabelShortcutButton } from './label-shortcut-button.component';

interface LabelShortcutItemProps {
    label: Label;
    isLast: boolean;
    onClick: (label: Label) => void;
    isDisabled: boolean;
}

export const LabelShortcutItem = ({ label, isLast, onClick, isDisabled }: LabelShortcutItemProps): JSX.Element => {
    const labelRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const element = labelRef.current;
        if (isLast && isFunction(element?.scrollIntoView)) {
            element?.scrollIntoView();
        }
    }, [isLast]);

    return (
        <div ref={labelRef} role='listitem'>
            <LabelShortcutButton id={`label-${label.id}`} onPress={() => onClick(label)} isDisabled={isDisabled}>
                <LabelColorThumb label={label} id={`${label.id}-color-thumb-label-item`} marginEnd={'size-50'} />
                <TruncatedText maxWidth={'size-2400'}>{label.name}</TruncatedText>
            </LabelShortcutButton>
        </div>
    );
};
