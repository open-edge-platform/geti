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

import { Flex, Text } from '@adobe/react-spectrum';
import { SpectrumActionButtonProps } from '@react-types/button';
import Checkmark from '@spectrum-icons/workflow/Checkmark';

import { ActionButton } from '../../../../shared/components/button/button.component';

import classes from './select-domain-button.module.scss';

interface SelectDomainButtonProps extends SpectrumActionButtonProps {
    id: string;
    text: string;
    select: () => void;
    isSelected: boolean;
    isDisabled?: boolean;
    taskNumber: number;
    isDone?: boolean;
}

export const SelectDomainButton = ({
    text,
    select,
    isSelected,
    isDisabled = false,
    id,
    isDone = false,
    taskNumber,
    ...props
}: SelectDomainButtonProps): JSX.Element => {
    return (
        <Flex direction={'column'} alignItems={'center'} height={'100%'}>
            <Flex height={'100%'} alignItems={'center'}>
                <ActionButton
                    id={id}
                    onPress={select}
                    margin={'size-150'}
                    UNSAFE_className={isSelected ? classes.selected : isDone ? classes.checked : classes.stepButton}
                    isDisabled={isDisabled}
                    aria-label={`Button domain${isSelected ? ' selected' : ''}`}
                    {...props}
                >
                    {isDone ? <Checkmark size='S' /> : taskNumber}
                </ActionButton>
            </Flex>
            <Text>{text}</Text>
        </Flex>
    );
};
