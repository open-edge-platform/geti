// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Flex, Text, type ActionButtonProps } from '@geti/ui';
import { Checkmark } from '@geti/ui/icons';

import classes from './select-domain-button.module.scss';

interface SelectDomainButtonProps extends ActionButtonProps {
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
