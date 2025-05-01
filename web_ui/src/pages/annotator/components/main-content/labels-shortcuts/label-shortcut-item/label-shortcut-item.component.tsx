// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { LabelColorThumb } from '@shared/components/label-color-thumb/label-color-thumb.component';
import { TruncatedText } from '@shared/components/truncated-text/truncated-text.component';
import isFunction from 'lodash/isFunction';

import { Label } from '../../../../../../core/labels/label.interface';
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
