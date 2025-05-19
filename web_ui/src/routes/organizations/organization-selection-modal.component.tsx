// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, Content, Dialog, DialogContainer, dimensionValue, Divider, Flex, Heading, Text } from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { noop } from 'lodash-es';

import { getErrorMessage } from '../../core/services/utils';
import { useOnboardUserMutation } from '../../core/users/hook/use-onboard-user-mutation.hook';
import { useProfileQuery } from '../../core/users/hook/use-profile.hook';
import { OrganizationMetadata } from '../../core/users/services/onboarding-service.interface';
import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { formatUtcToLocal } from '../../shared/utils';
import { isInvitedOrganization, isOrganizationVisible, isUserInvitedInOrg } from './util';

interface OrganizationSelectionModalProps {
    title: string;
    description: string;
    organizations: OrganizationMetadata[];
    onSelectedOrganization: (id: string) => void;
}

export const OrganizationSelectionModal = ({
    title,
    description,
    organizations,
    onSelectedOrganization,
}: OrganizationSelectionModalProps) => {
    const { addNotification } = useNotification();
    const { data: profileData } = useProfileQuery();
    const onboardUserMutation = useOnboardUserMutation();
    const dialogState = useOverlayTriggerState({ defaultOpen: true });
    const hasAcceptedUserTermsAndConditions = profileData?.hasAcceptedUserTermsAndConditions ?? false;

    const handlerOnboardUserMutation = (organizationId: string) => {
        onboardUserMutation.mutate(
            { organizationId, userConsentIsGiven: true },
            {
                onError: (error) => {
                    addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
                },
                onSuccess: () => {
                    selectAndClose(organizationId);
                },
            }
        );
    };

    const selectAndClose = (organizationId: string) => {
        onSelectedOrganization(organizationId);
        dialogState.toggle();
    };

    const handlerSelectOrganization = (organization: OrganizationMetadata) => {
        if (
            hasAcceptedUserTermsAndConditions &&
            (isInvitedOrganization(organization) || isUserInvitedInOrg(organization))
        ) {
            handlerOnboardUserMutation(organization.id);
        } else {
            selectAndClose(organization.id);
        }
    };

    return (
        <DialogContainer onDismiss={noop}>
            {dialogState.isOpen && (
                <Dialog>
                    <Heading level={2}>{title}</Heading>
                    <Divider size={'S'} />

                    <Content>
                        <Text
                            UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}
                        >{`${description} Please select the organization you wish to access now.`}</Text>

                        <Flex
                            gap={'size-300'}
                            marginTop={'size-300'}
                            direction={'column'}
                            UNSAFE_style={{
                                padding: dimensionValue('size-300'),
                                backgroundColor: 'var(--spectrum-global-color-gray-50)',
                            }}
                        >
                            {organizations.filter(isOrganizationVisible).map((organization) => (
                                <Flex
                                    key={organization.id}
                                    minHeight={'size-1250'}
                                    alignItems={'center'}
                                    justifyContent={'space-between'}
                                    UNSAFE_style={{
                                        border: `1px solid var(--spectrum-global-color-gray-200)`,
                                        padding: dimensionValue('size-300'),
                                        backgroundColor: 'var(--spectrum-global-color-gray-75)',
                                    }}
                                >
                                    <Flex direction={'column'} maxWidth={'size-3600'} gap={'size-125'}>
                                        <Text
                                            UNSAFE_style={{
                                                fontWeight: 500,
                                                wordBreak: 'break-all',
                                                fontSize: dimensionValue('size-200'),
                                            }}
                                        >
                                            {organization.name}
                                        </Text>
                                        <Text UNSAFE_style={{ fontWeight: 400, fontSize: dimensionValue('size-150') }}>
                                            Organization created on{' '}
                                            {formatUtcToLocal(organization.createdAt, 'DD MMM YYYY')}
                                        </Text>
                                    </Flex>
                                    <Button
                                        variant='secondary'
                                        minWidth={'size-2000'}
                                        isPending={onboardUserMutation.isPending}
                                        aria-label={`select organization ${organization.id}`}
                                        UNSAFE_style={{ borderRadius: 0 }}
                                        onPress={() => handlerSelectOrganization(organization)}
                                    >
                                        Go to organization
                                    </Button>
                                </Flex>
                            ))}
                        </Flex>
                    </Content>
                </Dialog>
            )}
        </DialogContainer>
    );
};
