// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { User } from '@geti/core/src/users/users.interface';

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
