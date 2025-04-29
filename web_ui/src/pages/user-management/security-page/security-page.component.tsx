// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Heading, Text } from '@adobe/react-spectrum';

import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { ShowForOnPrem } from '../../../shared/components/show-for-onprem/show-for-onprem.component';
import { ChangePasswordPopup } from '../profile-page/change-password-popup/change-password-popup.component';
import { PreviousSignIn } from './previous-sign-in.component';

import classes from './security-page.module.scss';

interface SecurityPageProps {
    activeUserId: string;
}
export const SecurityPage = ({ activeUserId }: SecurityPageProps): JSX.Element => {
    const isSaaS = useIsSaasEnv();

    return (
        <Flex
            width={'100%'}
            alignItems={'center'}
            justifyContent={'center'}
            direction={'column'}
            UNSAFE_className={classes.securityPageWrapper}
        >
            <ShowForOnPrem>
                <Flex width={'100%'} justifyContent={'space-between'} alignItems={'center'}>
                    <Heading id={'password-title'} margin={0}>
                        Password
                    </Heading>
                </Flex>
                <Flex width={'100%'} marginBottom={'size-150'}>
                    <Text UNSAFE_className={classes.text} id={'change-password-description'}>
                        Set a unique password to protect your personal Intel® Geti™ account.
                    </Text>
                </Flex>
                <ChangePasswordPopup userId={activeUserId} />
                {isSaaS && <Divider size={'S'} marginY={'size-300'} />}
            </ShowForOnPrem>
            {isSaaS && <PreviousSignIn />}
        </Flex>
    );
};
