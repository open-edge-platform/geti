// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { isNil } from 'lodash-es';
import { useLocation, useNavigate } from 'react-router-dom';

import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { isActiveOrganization, isUserActivatedInOrg, isUserInvitedInOrg } from '../../../routes/organizations/util';
import { hasEqualId } from '../../../shared/utils';
import { paths } from '../../../../packages/core/src/services/routes';
import { getErrorMessage } from '../../services/utils';
import { GENERAL_SETTINGS_KEYS } from '../../user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../user-settings/hooks/use-global-settings.hook';
import { getSettingsOfType } from '../../user-settings/utils';
import { useOnboardUserMutation } from '../../users/hook/use-onboard-user-mutation.hook';
import { useProfileQuery } from '../../users/hook/use-profile.hook';

const removeLastForwardSlash = (text: string) => text.replace(/\/$/, '');

export const useSelectedOrganization = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { organizationId } = useOrganizationIdentifier();
    const { addNotification } = useNotification();
    const userGlobalSettings = useUserGlobalSettings();
    const onboardUserMutation = useOnboardUserMutation();
    const { data, ...profileResponse } = useProfileQuery();

    const isOnboarding = useRef(false);

    const globalSettings = getSettingsOfType(userGlobalSettings.config, GENERAL_SETTINGS_KEYS);
    const chosenOrganizationId: string | null = globalSettings[GENERAL_SETTINGS_KEYS.CHOSEN_ORGANIZATION].value;

    const organizations = data?.organizations ?? [];
    const originalUrl = `${removeLastForwardSlash(location.pathname)}${location.search}`;
    const hasOrganizationID = !isNil(organizationId);
    const defaultOrganization = organizations.at(0);
    const hasMultipleOrganizations = organizations.length > 1;
    const hasAcceptedUserTermsAndConditions = data?.hasAcceptedUserTermsAndConditions ?? false;
    const isUserAutoOnboardingEnabled = hasAcceptedUserTermsAndConditions && !isOnboarding.current;
    const chosenOrganization = organizations.find(hasEqualId(chosenOrganizationId));
    const hasChosenActiveOrganization =
        chosenOrganization && isActiveOrganization(chosenOrganization) && !originalUrl.includes(chosenOrganization.id);

    const selectSingleOrganizationByDefault =
        !hasMultipleOrganizations && defaultOrganization && defaultOrganization.id !== organizationId;

    const handleOnboardUserMutation = (id: string, onSuccess: () => void) => {
        isOnboarding.current = true;

        onboardUserMutation.mutate(
            { organizationId: id, userConsentIsGiven: true },
            {
                onSuccess,
                onError: (error) => {
                    addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
                },
                onSettled: () => {
                    isOnboarding.current = false;
                },
            }
        );
    };

    useEffect(() => {
        if (hasChosenActiveOrganization) {
            const route = paths.organization.index({ organizationId: chosenOrganization.id });
            navigate(`${route}${originalUrl}`);
            return;
        }

        if (selectSingleOrganizationByDefault) {
            const route = paths.organization.index({ organizationId: defaultOrganization.id });
            const finalRoute = hasOrganizationID ? route : `${route}${originalUrl}`;

            if (isUserActivatedInOrg(defaultOrganization)) {
                navigate(finalRoute);
            }

            if (isUserInvitedInOrg(defaultOrganization) && isUserAutoOnboardingEnabled) {
                handleOnboardUserMutation(defaultOrganization.id, () => {
                    navigate(finalRoute);
                });
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [
        defaultOrganization,
        hasOrganizationID,
        navigate,
        organizationId,
        originalUrl,
        isUserAutoOnboardingEnabled,
        hasChosenActiveOrganization,
        selectSingleOrganizationByDefault,
    ]);

    return {
        ...profileResponse,
        organizations,
        hasMultipleOrganizations,
        selectedOrganization: organizations.find(hasEqualId(String(organizationId))) ?? null,
        setSelectedOrganization: (id: string) => {
            const newOrganization = data?.organizations.find(hasEqualId(id));

            if (isNil(newOrganization)) {
                return;
            }

            userGlobalSettings.saveConfig({
                ...userGlobalSettings.config,
                [GENERAL_SETTINGS_KEYS.CHOSEN_ORGANIZATION]: { value: newOrganization.id },
            });
            navigate(paths.organization.index({ organizationId: newOrganization.id }));
        },
    };
};
