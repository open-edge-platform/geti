// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { User } from '../../../core/users/users.interface';

const Fullname = ({ user }: { user: User }) => {
    const firstName = user.firstName;
    const lastName = user.lastName;
    const name = `${firstName} ${lastName}`;

    return <>{name}</>;
};

export const FullnameWithLoading = ({ user, isLoading }: { user: User | undefined; isLoading: boolean }) => {
    if (isLoading) {
        return <>Loading ...</>;
    }

    if (user === undefined) {
        return <>Unknown user</>;
    }

    return <Fullname user={user} />;
};
