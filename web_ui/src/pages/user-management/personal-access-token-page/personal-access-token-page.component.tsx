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

import { Divider, Flex, Heading, Text, View } from '@adobe/react-spectrum';
import { useOverlayTriggerState } from '@react-stately/overlays';
import isEmpty from 'lodash/isEmpty';

import { usePersonalAccessToken } from '../../../core/personal-access-tokens/hooks/use-personal-access-token.hook';
import { Button } from '../../../shared/components/button/button.component';
import { CreatePersonalAccessTokenDialog } from './components/create-personal-access-token-dialog.component';
import { PersonalAccessTokensTable } from './components/personal-access-tokens-table.component';

interface PersonalAccessTokenPageProps {
    activeUserId: string;
    organizationId: string;
}

export const PersonalAccessTokenPage = ({
    activeUserId,
    organizationId,
}: PersonalAccessTokenPageProps): JSX.Element => {
    const { useGetPersonalAccessTokensQuery } = usePersonalAccessToken();
    const { data, isPending } = useGetPersonalAccessTokensQuery({ organizationId, userId: activeUserId });
    const createPersonalAccessTokenDialogState = useOverlayTriggerState({});
    const personalAccessTokens = data?.personalAccessTokens;

    return (
        <View>
            <Flex justifyContent={'space-between'} alignItems={'start'} direction={'column'}>
                <Heading margin={0} marginBottom={'size-50'}>
                    Create Personal Access Token
                </Heading>
                <Text id={'general-warning-message-id'} UNSAFE_style={{ fontWeight: '100' }}>
                    When you use an Personal Access Token in your application, ensure that it is kept secure during both
                    storage and transmission
                </Text>
                <Button
                    id={'open-create-api-token-dialog-button-id'}
                    variant={'accent'}
                    onPress={createPersonalAccessTokenDialogState.open}
                    isDisabled={isPending}
                    marginTop={'size-250'}
                >
                    Create
                </Button>
            </Flex>
            {!isEmpty(personalAccessTokens) && (
                <View>
                    <Divider size='M' marginTop={'size-600'} />
                    <Heading marginY={'size-400'}>Existing tokens</Heading>
                    <PersonalAccessTokensTable tokens={personalAccessTokens} isLoading={isPending} />
                </View>
            )}
            <CreatePersonalAccessTokenDialog
                triggerState={createPersonalAccessTokenDialogState}
                userId={activeUserId}
                organizationId={organizationId}
            />
        </View>
    );
};
