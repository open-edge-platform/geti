// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { Label } from '../../../../../core/labels/label.interface';
import { PressableElement } from '../../../../../shared/components/action-element/action-element.component';
import { LabelColorThumb } from '../../../../../shared/components/label-color-thumb/label-color-thumb.component';
import { TruncatedText } from '../../../../../shared/components/truncated-text/truncated-text.component';

interface LabelTagProps {
    id?: string;
    label: Label;
    onClick?: () => void;
    isPointer?: boolean;
}

export const LabelTag = ({ id, label, onClick, isPointer }: LabelTagProps): JSX.Element => {
    return (
        <Flex alignItems='center' gap='size-75'>
            <LabelColorThumb label={label} size={7} id={`${id}-color`} />

            <TooltipTrigger>
                <PressableElement
                    id={id}
                    onPress={onClick}
                    maxWidth={'size-2400'}
                    UNSAFE_style={{ cursor: isPointer ? 'pointer' : 'auto' }}
                >
                    <TruncatedText>{label.name}</TruncatedText>
                </PressableElement>
                <Tooltip>{label.name}</Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};
