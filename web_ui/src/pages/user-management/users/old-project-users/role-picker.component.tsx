// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, Key } from 'react';

import { Item, Picker } from '@geti/ui';
import { capitalize, isEmpty } from 'lodash-es';

import { USER_ROLE } from '../../../../core/users/users.interface';

interface RolePickerProps<T> extends Omit<ComponentProps<typeof Picker>, 'children'> {
    roles: T[];
    selectedRole: T | undefined;
    setSelectedRole: (user: T) => void;
    emptyItem?: string;
    testId?: string;
    options?: { showLabel?: boolean };
}

export const RolePicker = <T extends USER_ROLE>({
    roles,
    selectedRole,
    setSelectedRole,
    emptyItem,
    options = { showLabel: true },
    testId = 'roles-add-user',
    ...pickerProps
}: RolePickerProps<T>) => {
    const rolesItems = roles.map((role) => ({ key: role, text: role }));
    const items = isEmpty(emptyItem) ? rolesItems : [...rolesItems, { key: '', text: emptyItem }];

    const onSelectionChange = (key: Key) => {
        setSelectedRole(key as T);
    };

    return (
        <Picker
            {...pickerProps}
            label={options.showLabel ? 'Role' : undefined}
            placeholder={'Select a role'}
            items={items}
            id='roles-add-user'
            data-testid={testId}
            onSelectionChange={onSelectionChange}
            selectedKey={selectedRole ?? ''}
        >
            {(item) => (
                <Item key={item.key} textValue={item.text}>
                    {capitalize(item.text)}
                </Item>
            )}
        </Picker>
    );
};
