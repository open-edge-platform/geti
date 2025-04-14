// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@adobe/react-spectrum';

import { usePreviousSignIn } from '../../../shared/hooks/use-previous-sign-in.hook';

import classes from './security-page.module.scss';

export const PreviousSignIn = (): JSX.Element => {
    const { lastLoginDate } = usePreviousSignIn();

    if (!lastLoginDate) {
        return <></>;
    }

    return (
        <Flex width={'100%'} direction={'column'}>
            <Text>Previous sign-in</Text>
            <Text UNSAFE_className={classes.text}>{lastLoginDate}</Text>
        </Flex>
    );
};
