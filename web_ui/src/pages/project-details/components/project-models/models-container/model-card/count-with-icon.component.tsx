// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Flex, Text } from '@geti/ui';

import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

import classes from './model-card.module.scss';

interface CountWithIconProps {
    id: string;
    count: number;
    text: string;
    icon: ReactNode;
}

export const CountWithIcon = ({ id, icon, count, text }: CountWithIconProps): JSX.Element => {
    const message = count === 1 ? text : text + 's';

    return (
        <Flex alignItems={'center'} gap={'size-50'} UNSAFE_className={classes.countWithIcon}>
            {icon}
            <Text
                id={`${idMatchingFormat(text)}-count--${id}-id`}
                data-testid={`${idMatchingFormat(text)}-count-${id}-id`}
            >{`${count} ${message}`}</Text>
        </Flex>
    );
};
