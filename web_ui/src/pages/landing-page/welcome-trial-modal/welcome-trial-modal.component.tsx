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

import { DialogContainer, Flex, Heading, Text } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import sum from 'lodash/sum';

import { FireWorks } from '../../../assets/images';
import { useProducts } from '../../../core/credits/products/hooks/use-products.hook';
import { useSubscriptions } from '../../../core/credits/subscriptions/hooks/use-subscription-api.hook';
import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { GLOBAL_MODALS_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../core/user-settings/hooks/use-global-settings.hook';
import { getSettingsOfType } from '../../../core/user-settings/utils';
import { useProfileQuery } from '../../../core/users/hook/use-profile.hook';
import { useUsers } from '../../../core/users/hook/use-users.hook';
import { isOrganizationAdmin } from '../../../core/users/user-role-utils';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { Button } from '../../../shared/components/button/button.component';
import { WelcomingCreditsDetails } from './welcoming-credits-details.component';

import classes from './welcome-trial-modal.module.scss';

interface UseCredits {
    initCredits: number;
    monthlyRenewalCredits: number | null;
    creditsDataLoaded: boolean;
    creditsDataError: boolean;
}

const useCredits = (organizationId: string): UseCredits => {
    const { useGetActiveSubscriptionQuery } = useSubscriptions();
    const {
        data: activeSubscription,
        isSuccess: isSuccessSubscriptions,
        isError: isErrorSubscriptions,
    } = useGetActiveSubscriptionQuery({
        organizationId,
    });
    const { useGetProductQuery } = useProducts();
    const {
        data: products,
        isSuccess: isSuccessProducts,
        isError: isErrorProducts,
    } = useGetProductQuery(activeSubscription?.productId ?? 0, {
        enabled: activeSubscription !== undefined,
    });

    const welcomingCredits = sum(products?.productPolicies.map((policy) => policy.initAmount));

    const renewableCredits = sum(products?.productPolicies.map((policy) => policy.renewableAmount));

    return {
        initCredits: welcomingCredits,
        monthlyRenewalCredits: renewableCredits,
        creditsDataLoaded: isSuccessSubscriptions && isSuccessProducts,
        creditsDataError: isErrorSubscriptions || isErrorProducts,
    };
};

export const WelcomeTrialModal = () => {
    const settings = useUserGlobalSettings();
    const { organizationId } = useOrganizationIdentifier();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const { data: profileData } = useProfileQuery();
    const { initCredits, monthlyRenewalCredits, creditsDataLoaded, creditsDataError } = useCredits(organizationId);
    const { useGetUsersQuery } = useUsers();
    const { users, isSuccess: usersDataLoaded, isError: usersDataError } = useGetUsersQuery(organizationId);

    const creditSystemConfig = getSettingsOfType(settings.config, GLOBAL_MODALS_KEYS);
    const isModalEnabled = creditSystemConfig[GLOBAL_MODALS_KEYS.WELCOME_MODAL].isEnabled === true;

    const isModalOpen =
        FEATURE_FLAG_CREDIT_SYSTEM && isModalEnabled && profileData?.hasAcceptedUserTermsAndConditions === true;

    const dismissModal = async () => {
        await settings.saveConfig({ ...settings.config, [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: { isEnabled: false } });
    };

    // We only want to show the welcoming credits to the organization admin that created the organization
    const showWelcomingCredits = users?.length === 1 && users.at(0) && isOrganizationAdmin(users[0], organizationId);

    // Wait for all data to be loaded before showing the modal
    if (!creditsDataLoaded || !usersDataLoaded) {
        return <></>;
    }

    // In case of any api errors, we dismiss the modal
    if ((creditsDataError || usersDataError) && isModalOpen) {
        dismissModal();
    }

    return (
        <DialogContainer onDismiss={dismissModal}>
            {isModalOpen && (
                <Flex direction={'column'} alignItems={'center'} UNSAFE_className={classes.container}>
                    <Heading UNSAFE_className={classes.primaryTitle}>Welcome to Intel® Geti™</Heading>
                    <Heading UNSAFE_className={classes.secondaryTitle}>Powerful AI For Everyone</Heading>
                    <Text UNSAFE_className={classes.description}>
                        Start today with exploring the world of computer vision
                    </Text>
                    <WelcomingCreditsDetails
                        initCredits={showWelcomingCredits ? initCredits : null}
                        monthlyRenewalCredits={monthlyRenewalCredits}
                    />
                    <FireWorks />
                    <Button
                        width={'100%'}
                        variant={'accent'}
                        isDisabled={settings.isSavingConfig}
                        UNSAFE_style={{ fontSize: dimensionValue('size-200'), paddingTop: dimensionValue('size-50') }}
                        onPress={dismissModal}
                    >
                        Start exploring now
                    </Button>
                </Flex>
            )}
        </DialogContainer>
    );
};
