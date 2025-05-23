// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key, ReactNode } from 'react';

import { paths } from '@geti/core/src/services/routes';
import { HelpIcon } from '@geti/ui/icons';
import { ValueType } from '@opentelemetry/api';
import { Link } from 'react-router-dom';

import { useAnalytics } from '../../../../../analytics/analytics-provider.component';
import { getMetricName } from '../../../../../analytics/metrics';
import { CONTACT_SUPPORT as CONTACT_SUPPORT_URL } from '../../../../../core/const';
import { useDocsUrl } from '../../../../../hooks/use-docs-url/use-docs-url.hook';
import { useOrganizationIdentifier } from '../../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { useResetAllTutorials } from '../../../../hooks/use-tutorial-enablement.hook';
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

const ActionLink: FC<{ children: ReactNode; to: string }> = ({ children, to }) => {
    return (
        <Link to={to} className={classes.link} viewTransition>
            {children}
        </Link>
    );
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
                    text: <ActionLink to={docsUrl}>{HelpActionsItems.USER_GUIDE}</ActionLink>,
                },
                {
                    id: HelpActionsItems.ABOUT,
                    text: (
                        <ActionLink to={paths.organization.about({ organizationId })}>
                            {HelpActionsItems.ABOUT}
                        </ActionLink>
                    ),
                },
                {
                    id: HelpActionsItems.RESET_HELP_DIALOGS,
                    text: HelpActionsItems.RESET_HELP_DIALOGS,
                },
                {
                    id: HelpActionsItems.CONTACT_SUPPORT,
                    text: <ActionLink to={CONTACT_SUPPORT_URL}>{HelpActionsItems.CONTACT_SUPPORT}</ActionLink>,
                },
                {
                    id: HelpActionsItems.REST_API_SPECS,
                    text: <ActionLink to={paths.restApiSpecs({})}>{HelpActionsItems.REST_API_SPECS}</ActionLink>,
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
