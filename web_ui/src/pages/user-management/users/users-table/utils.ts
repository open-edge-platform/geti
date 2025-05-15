// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty } from 'lodash-es';

import { User } from '../../../../core/users/users.interface';

export const getUserFullName = (firstName: string, lastName: string) => {
    return isEmpty(firstName) || isEmpty(lastName) ? `${lastName}${firstName}` : `${lastName}, ${firstName}`;
};

export const getFullNameFromUser = (user: User | undefined): string => {
    if (!user) {
        return 'Unknown user';
    }

    return getNameIdentifier(user);
};

const getNameIdentifier = (user: User): string => {
    const { firstName, lastName, email } = user;

    return !firstName && !lastName ? email : getFullNameFromName(firstName, lastName);
};

export const getFullNameFromName = (firstName: string, lastName: string): string => {
    return `${firstName} ${lastName}`;
};
