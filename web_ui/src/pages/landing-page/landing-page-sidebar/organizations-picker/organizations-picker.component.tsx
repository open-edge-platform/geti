// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { Flex, Item, ListBox, Picker, View } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { isNil } from 'lodash-es';

import { useSelectedOrganization } from '../../../../core/organizations/hook/use-selected-organization.hook';
import { getErrorMessage } from '../../../../core/services/utils';
import { useOnboardUserMutation } from '../../../../core/users/hook/use-onboard-user-mutation.hook';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import {
    isInvitedOrganization,
    isOrganizationVisible,
    isUserInvitedInOrg,
} from '../../../../routes/organizations/util';
import { CustomPopover } from '../../../../shared/components/custom-popover/custom-popover.component';
import { PhotoPlaceholder } from '../../../../shared/components/photo-placeholder/photo-placeholder.component';
import { QuietToggleButton } from '../../../../shared/components/quiet-button/quiet-toggle-button.component';
import { hasEqualId, isNonEmptyString } from '../../../../shared/utils';

interface OrganizationsPickerProps {
    isLargeSize: boolean;
}

export const OrganizationsPicker = ({ isLargeSize }: OrganizationsPickerProps): JSX.Element => {
    const triggerRef = useRef(null);
    const { addNotification } = useNotification();
    const onboardUserMutation = useOnboardUserMutation();
    const organizationsPopoverState = useOverlayTriggerState({});
    const { selectedOrganization, organizations, isLoading, setSelectedOrganization, hasMultipleOrganizations } =
        useSelectedOrganization();

    const orgName = selectedOrganization?.name ?? '';
    const selectedKey = String(selectedOrganization?.id);
    const visibleOrganizations = organizations.filter(isOrganizationVisible);

    const handlerOnboardUserMutation = (organizationId: string) => {
        onboardUserMutation.mutate(
            { organizationId, userConsentIsGiven: true },
            {
                onError: (error) => {
                    addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
                },
                onSuccess: () => {
                    setSelectedOrganization(organizationId);
                },
            }
        );
    };

    const handlerSelectOrganization = (organizationId: string) => {
        const newOrganization = organizations.find(hasEqualId(organizationId));

        if (isNil(newOrganization)) {
            return;
        }

        if (isInvitedOrganization(newOrganization) || isUserInvitedInOrg(newOrganization)) {
            handlerOnboardUserMutation(newOrganization.id);
        } else {
            setSelectedOrganization(newOrganization.id);
        }
    };

    if (!hasMultipleOrganizations) {
        return <></>;
    }

    if (isLargeSize) {
        return (
            <Flex
                gap={'size-125'}
                marginBottom={'size-300'}
                UNSAFE_style={{ padding: `0px ${dimensionValue('size-350')}` }}
            >
                <PhotoPlaceholder
                    name={orgName}
                    email={orgName}
                    width={'size-400'}
                    height={'size-400'}
                    borderRadius={'20%'}
                />

                <Picker
                    id={`selected-org-${selectedOrganization?.id}`}
                    isDisabled={isLoading || onboardUserMutation.isPending}
                    aria-label={'organizations selection'}
                    defaultSelectedKey={selectedKey}
                    items={visibleOrganizations}
                    isQuiet
                    onSelectionChange={(key) => {
                        selectedOrganization?.id !== String(key) && handlerSelectOrganization(String(key));
                    }}
                >
                    {(item) => <Item>{item.name}</Item>}
                </Picker>
            </Flex>
        );
    }
    /* The mobile version of the Picker is only visible on devices 
     smaller than 700px (using useIsMobileDevice()). This solution simulates it on tablet sizes. */
    return (
        <>
            <QuietToggleButton
                ref={triggerRef}
                width={'100%'}
                marginBottom={'size-300'}
                isDisabled={isLoading || onboardUserMutation.isPending}
                id={`selected-org-${selectedOrganization?.id}`}
                aria-label={'organizations selection'}
                onPress={organizationsPopoverState.toggle}
                isSelected={organizationsPopoverState.isOpen}
            >
                <PhotoPlaceholder
                    name={orgName}
                    email={orgName}
                    width={'size-400'}
                    height={'size-400'}
                    borderRadius={'20%'}
                />
            </QuietToggleButton>

            <CustomPopover ref={triggerRef} state={organizationsPopoverState} placement='right top'>
                <View minWidth={'size-2000'}>
                    <ListBox
                        items={visibleOrganizations}
                        selectionMode='single'
                        defaultSelectedKeys={[selectedKey]}
                        onSelectionChange={(key) => {
                            if (key !== 'all') {
                                const iterator = key.values();
                                const newValue = iterator.next().value;
                                organizationsPopoverState.close();

                                isNonEmptyString(newValue) && handlerSelectOrganization(newValue);
                            }
                        }}
                    >
                        {(item) => <Item key={item.id}>{item.name}</Item>}
                    </ListBox>
                </View>
            </CustomPopover>
        </>
    );
};
