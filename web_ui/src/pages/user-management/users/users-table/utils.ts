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

import isEmpty from 'lodash/isEmpty';

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
