// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentProps, Key } from 'react';

import { Item, Picker } from '@adobe/react-spectrum';
import capitalize from 'lodash/capitalize';
import isEmpty from 'lodash/isEmpty';

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
