// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useMemo, useState } from 'react';

import { User } from '@geti/core/src/users/users.interface';
import { ComboBox, Item, useFilter } from '@geti/ui';

import { hasEqualId } from '../../../../shared/utils';
import { getFullNameFromUser } from '../users-table/utils';

interface SelectUserProps<T> {
    users: T[];
    selectedUser: T | undefined;
    setSelectedUser: (user: T | undefined) => void;
}

const getUserDisplayName = (user: User) => {
    const userFullName = getFullNameFromUser(user);

    if (userFullName === user.email) {
        return userFullName;
    } else {
        return `${userFullName} (${user.email})`;
    }
};

// CAUTION: this component does not work in React's strict mode
// To use this component in development either disable strict mode
// in `src/index.tsx`, or build the app with npm run build
export const SelectUser = <T extends User>({ users, selectedUser, setSelectedUser }: SelectUserProps<T>) => {
    const [showAll, setShowAll] = useState(false);

    const selectedKey = selectedUser?.id ?? null;
    const [filterValue, setFilterValue] = useState<string>('');

    const { contains } = useFilter({ sensitivity: 'base' });
    const filteredUsers = useMemo(
        () =>
            users.filter((item) => {
                const fullName = getFullNameFromUser(item);
                return contains(item.email, filterValue) || contains(fullName, filterValue);
            }),
        [users, filterValue, contains]
    );

    const onSelectionChange = (key: Key | null) => {
        const user = users.find(hasEqualId((key ?? '').toLocaleString()));
        setSelectedUser(user);
        setFilterValue(user ? getUserDisplayName(user) : '');
    };

    const onInputChange = (value: string) => {
        setShowAll(false);
        setFilterValue(value);
    };

    return (
        <ComboBox
            label='User'
            aria-label='select user'
            menuTrigger='focus'
            id={'select-user'}
            width={'auto'}
            items={showAll ? users : filteredUsers}
            onOpenChange={(isOpen, menuTrigger) => {
                // Show all items if menu is opened manually
                // i.e. by the arrow keys or trigger button
                if (menuTrigger === 'manual' && isOpen) {
                    setShowAll(true);
                }
            }}
            selectedKey={selectedKey}
            onSelectionChange={onSelectionChange}
            inputValue={filterValue}
            onInputChange={onInputChange}
        >
            {(item: T) => <Item textValue={item.email}>{getUserDisplayName(item)}</Item>}
        </ComboBox>
    );
};
