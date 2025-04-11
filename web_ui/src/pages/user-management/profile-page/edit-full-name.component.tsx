// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
