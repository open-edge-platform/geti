// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps } from 'react';

import { Flex, TextField } from '@adobe/react-spectrum';

import { MAX_NUMBER_OF_CHARACTERS } from '../users/utils';

interface EditFullNameProps extends ComponentProps<typeof TextField> {
    cssClass?: string;
    firstName: string;
    lastName: string;
    setFirstName: (name: string) => void;
    setLastName: (name: string) => void;
}

export const EditFullName = ({
    cssClass,
    firstName,
    lastName,
    setFirstName,
    setLastName,
    ...textFielProps
}: EditFullNameProps): JSX.Element => {
    return (
        <Flex gap={'size-400'}>
            <TextField
                type='text'
                id='first-name'
                name='firstname'
                label='First name'
                UNSAFE_className={cssClass}
                value={firstName}
                maxLength={MAX_NUMBER_OF_CHARACTERS}
                onChange={setFirstName}
                {...textFielProps}
            />
            <TextField
                type='text'
                id='last-name'
                name='lastname'
                label='Last name'
                UNSAFE_className={cssClass}
                value={lastName}
                maxLength={MAX_NUMBER_OF_CHARACTERS}
                onChange={setLastName}
                {...textFielProps}
            />
        </Flex>
    );
};
