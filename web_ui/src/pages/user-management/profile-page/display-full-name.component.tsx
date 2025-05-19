// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { TextField } from '@geti/ui';

import { getFullNameFromName } from '../users/users-table/utils';

import classes from './profile-page.module.scss';

interface DisplayFullNameProps {
    firstName: string;
    lastName: string;
}

export const DisplayFullName = ({ firstName, lastName }: DisplayFullNameProps): JSX.Element => {
    const fullName = getFullNameFromName(firstName, lastName);

    return (
        <TextField
            type='text'
            id='full-name'
            data-testid={'display-user-full-name'}
            label='Full name'
            value={fullName}
            isReadOnly
            UNSAFE_className={[classes.textFieldReadOnly, classes.textField].join(' ')}
            marginBottom='size-175'
        />
    );
};
