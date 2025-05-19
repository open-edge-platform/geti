// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { ActionButton, Flex } from '@geti/ui';

import { Close } from '../../../../../../assets/icons';
import { LinkButton } from '../../../../../../pages/create-project/components/project-labels-management/task-labels-management/new-label-tree-item/link-button/link-button.component';
import { HotkeyEditionField } from '../../label-edition-mode/hotkey-edition-field/hotkey-edition-field.component';
import { HotkeyLabel } from './hotkey-label.component';

interface HotkeyNameFieldProps {
    text: string;
    info?: string;
    error: string;
    value?: string;
    onChange: (value: string, dirty?: boolean) => void;
    gridArea?: string;
}

interface HotkeyDisplayFieldProps {
    value: string;
    error: string;
    onChange: (value: string, isDirty?: boolean) => void;
    onClose: () => void;
    gridArea?: string;
}

const HotkeyDisplayField = ({ value, onChange, onClose, error, gridArea }: HotkeyDisplayFieldProps): JSX.Element => {
    const clearField = () => {
        onChange('', false);
        onClose();
    };

    return (
        <Flex gap={'size-100'} alignItems={'center'} gridArea={gridArea}>
            <HotkeyLabel />
            <Flex>
                <HotkeyEditionField
                    value={value}
                    width='size-1100'
                    onChange={onChange}
                    aria-label={'edited hotkey'}
                    validationState={error ? 'invalid' : undefined}
                />
                <ActionButton
                    onPress={clearField}
                    id={`${value}-hotkey-close-button-id`}
                    data-testid='hotkey-close-button'
                >
                    <Close />
                </ActionButton>
            </Flex>
        </Flex>
    );
};

export const HotkeyNameField = ({
    value,
    onChange,
    text,
    info,
    error,
    gridArea,
}: HotkeyNameFieldProps): JSX.Element => {
    const [isInEditionMode, setIsInEditionMode] = useState(false);

    if (!value?.length) {
        return (
            <LinkButton
                text={text}
                isOpen={isInEditionMode}
                onOpen={() => setIsInEditionMode(true)}
                info={info}
                gridArea={gridArea}
                data-testid='hotkey-name-field'
            >
                <HotkeyDisplayField
                    value={value as string}
                    onChange={onChange}
                    error={error}
                    onClose={() => setIsInEditionMode(false)}
                />
            </LinkButton>
        );
    }

    return (
        <HotkeyDisplayField
            value={value}
            onChange={onChange}
            error={error}
            gridArea={gridArea}
            onClose={() => setIsInEditionMode(false)}
        />
    );
};
