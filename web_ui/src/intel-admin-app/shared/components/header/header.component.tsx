// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Divider, Heading } from '@adobe/react-spectrum';

interface HeaderProps {
    title: string;
}

export const Header: FC<HeaderProps> = ({ title }) => {
    return (
        <>
            <Heading level={2} margin={0} marginBottom={'size-300'}>
                {title}
            </Heading>

            <Divider size={'S'} marginBottom={'size-300'} />
        </>
    );
};
