// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, Divider, Flex, Heading, Text, View } from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { isEmpty } from 'lodash-es';

import { usePersonalAccessToken } from '../../../core/personal-access-tokens/hooks/use-personal-access-token.hook';
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
