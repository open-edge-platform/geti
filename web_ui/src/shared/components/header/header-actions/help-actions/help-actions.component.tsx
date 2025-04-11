// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key } from 'react';

import { ValueType } from '@opentelemetry/api';

import { useAnalytics } from '../../../../../analytics/analytics-provider.component';
import { getMetricName } from '../../../../../analytics/metrics';
import { HelpIcon } from '../../../../../assets/icons';
import { CONTACT_SUPPORT as CONTACT_SUPPORT_URL } from '../../../../../core/const';
import { paths } from '../../../../../core/services/routes';
import { useDocsUrl } from '../../../../../hooks/use-docs-url/use-docs-url.hook';
import { useOrganizationIdentifier } from '../../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { useResetAllTutorials } from '../../../../hooks/use-tutorial-enablement.hook';
import { RouterLink as Link } from '../../../router-link/router-link.component';
import { HeaderSubmenu } from '../header-submenu/header-submenu.component';

import classes from './help-actions.module.scss';

export enum HelpActionsItems {
    USER_GUIDE = 'User guide',
    ABOUT = 'About',
    RESET_HELP_DIALOGS = 'Reset help dialogs',
    CONTACT_SUPPORT = 'Contact support',
    REST_API_SPECS = 'REST API specification',
}

interface HelpActionsProps {
    isDarkMode: boolean;
}

interface UseCollectOpeningUserGuideMetric {
    collectOpeningUserGuide: () => void;
}

const useCollectOpeningUserGuideMetric = (): UseCollectOpeningUserGuideMetric => {
    const { meter } = useAnalytics();

    const collectOpeningUserGuide = () => {
        const userGuideCounter = meter?.createCounter(getMetricName('user_guide.visits'), {
            description: 'Metric for opening user guide from the help menu',
            valueType: ValueType.INT,
        });

        userGuideCounter?.add(1);
    };

    return {
        collectOpeningUserGuide,
    };
};

export const HelpActions = ({ isDarkMode }: HelpActionsProps): JSX.Element => {
    const docsUrl = useDocsUrl();
    const resetAll = useResetAllTutorials();
    const { organizationId } = useOrganizationIdentifier();
    const { collectOpeningUserGuide } = useCollectOpeningUserGuideMetric();

    const handleMenuAction = async (key: Key): Promise<void> => {
        if (key === HelpActionsItems.USER_GUIDE) {
            collectOpeningUserGuide();
        } else if (key === HelpActionsItems.RESET_HELP_DIALOGS) {
            await resetAll();
        }
    };

    const MENU_ITEMS = [
        {
            children: [
                {
                    id: HelpActionsItems.USER_GUIDE,
                    text: (
                        <Link to={docsUrl} UNSAFE_className={classes.link}>
                            {HelpActionsItems.USER_GUIDE}
                        </Link>
                    ),
                },
                {
                    id: HelpActionsItems.ABOUT,
                    text: (
                        <Link to={paths.organization.about({ organizationId })} UNSAFE_className={classes.link}>
                            {HelpActionsItems.ABOUT}
                        </Link>
                    ),
                },
                {
                    id: HelpActionsItems.RESET_HELP_DIALOGS,
                    text: HelpActionsItems.RESET_HELP_DIALOGS,
                },
                {
                    id: HelpActionsItems.CONTACT_SUPPORT,
                    text: (
                        <Link to={CONTACT_SUPPORT_URL} UNSAFE_className={classes.link}>
                            {HelpActionsItems.CONTACT_SUPPORT}
                        </Link>
                    ),
                },
                {
                    id: HelpActionsItems.REST_API_SPECS,
                    text: (
                        <Link to={paths.restApiSpecs({})} UNSAFE_className={classes.link}>
                            {HelpActionsItems.REST_API_SPECS}
                        </Link>
                    ),
                },
            ],
            id: 'docs-id',
        },
    ];

    return (
        <HeaderSubmenu
            ariaLabel={'Documentation actions'}
            items={MENU_ITEMS}
            icon={<HelpIcon width={15} />}
            onMenuAction={handleMenuAction}
            isDarkMode={isDarkMode}
        />
    );
};
