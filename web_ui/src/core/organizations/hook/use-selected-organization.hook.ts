// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import isNil from 'lodash/isNil';
import { useLocation, useNavigate } from 'react-router-dom';

import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { isUserActivatedInOrg, isUserInvitedInOrg } from '../../../routes/organizations/util';
import { hasEqualId } from '../../../shared/utils';
import { paths } from '../../services/routes';
import { getErrorMessage } from '../../services/utils';
import { useOnboardUserMutation } from '../../users/hook/use-onboard-user-mutation.hook';
import { useProfileQuery } from '../../users/hook/use-profile.hook';

const removeLastForwardSlash = (text: string) => text.replace(/\/$/, '');

export const useSelectedOrganization = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { organizationId } = useOrganizationIdentifier();
    const { addNotification } = useNotification();
    const onboardUserMutation = useOnboardUserMutation();
    const { data, ...profileResponse } = useProfileQuery();

    const isOnboarding = useRef(false);

    const organizations = data?.organizations ?? [];
    const originalUrl = `${removeLastForwardSlash(location.pathname)}${location.search}`;
    const hasOrganizationID = !isNil(organizationId);
    const defaultOrganization = organizations.at(0);
    const hasMultipleOrganizations = organizations.length > 1;
    const hasAcceptedUserTermsAndConditions = data?.hasAcceptedUserTermsAndConditions ?? false;
    const isUserAutoOnboardingEnabled = hasAcceptedUserTermsAndConditions && !isOnboarding.current;

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

            navigate(paths.organization.index({ organizationId: newOrganization.id }));
        },
    };
};
