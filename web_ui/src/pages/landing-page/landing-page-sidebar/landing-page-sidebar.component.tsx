// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Link as SpectrumLink, useMediaQuery, View } from '@geti/ui';
import { InfoOutline, Policy, ProjectsIcon, UserIcon } from '@geti/ui/icons';
import { isLargeSizeQuery } from '@geti/ui/theme';
import { Link } from 'react-router-dom';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { paths } from '../../../core/services/routes';
import { useFirstWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { MenuItemImage } from '../../../shared/components/menu-item-image/menu-item-image.component';
import { MenuOption } from '../../../shared/components/menu-option.interface';
import { ShowForOnPrem } from '../../../shared/components/show-for-onprem/show-for-onprem.component';
import { SidebarMenu } from '../../../shared/components/sidebar-menu/sidebar-menu.component';
import { idMatchingFormat } from '../../../test-utils/id-utils';
import { OrganizationsPicker } from './organizations-picker/organizations-picker.component';
import { StorageUsage } from './storage-usage/storage-usage.component';

import classes from './landing-page-sidebar.module.scss';

enum LandingPageMenuOptions {
    PROJECTS = 'Projects',
    ACCOUNT = 'Account',
    LEARN = 'Learn',
    ABOUT = 'About',
    USERS = 'Users',
}

export const LandingPageSidebar = (): JSX.Element => {
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();

    const { FEATURE_FLAG_STORAGE_SIZE_COMPUTATION } = useFeatureFlags();

    const options: MenuOption[][] = [
        [
            {
                id: idMatchingFormat(LandingPageMenuOptions.PROJECTS),
                name: LandingPageMenuOptions.PROJECTS,
                url: paths.home({ organizationId, workspaceId }),
                ariaLabel: LandingPageMenuOptions.PROJECTS,
                icon: (
                    <MenuItemImage>
                        <ProjectsIcon width={'100%'} height={'100%'} />
                    </MenuItemImage>
                ),
            },
            {
                id: idMatchingFormat(LandingPageMenuOptions.ACCOUNT),
                name: LandingPageMenuOptions.ACCOUNT,
                url: paths.account.index({ organizationId }),
                ariaLabel: LandingPageMenuOptions.ACCOUNT,
                icon: (
                    <MenuItemImage>
                        <UserIcon width={'100%'} height={'100%'} />
                    </MenuItemImage>
                ),
            },
            {
                id: idMatchingFormat(LandingPageMenuOptions.ABOUT),
                name: LandingPageMenuOptions.ABOUT,
                url: paths.organization.about({ organizationId }),
                ariaLabel: LandingPageMenuOptions.ABOUT,
                icon: (
                    <MenuItemImage>
                        <InfoOutline width={'100%'} height={'100%'} />
                    </MenuItemImage>
                ),
            },
        ],
    ];

    const isLargeSize = useMediaQuery(isLargeSizeQuery);

    return (
        <Flex direction={'column'} height={'100%'}>
            <Flex justifyContent={'space-between'} direction={'column'} height={'100%'} marginTop={'size-600'}>
                <View>
                    <OrganizationsPicker isLargeSize={isLargeSize} />
                    <SidebarMenu options={options} id={'landing-page'} />
                </View>
                <Flex direction={'column'} width={'100%'} gap={isLargeSize ? 'size-150' : 'size-100'}>
                    <ShowForOnPrem>{FEATURE_FLAG_STORAGE_SIZE_COMPUTATION && <StorageUsage />}</ShowForOnPrem>
                    <Divider size='S' UNSAFE_className={classes.sidebarDivider} />
                    {isLargeSize ? (
                        <Flex UNSAFE_className={classes.sidebarFooter}>
                            <SpectrumLink UNSAFE_className={classes.footerLink}>
                                <Link to={paths.organization.about({ organizationId })} viewTransition>
                                    Terms of use <Divider size={'S'} orientation={'vertical'} /> Privacy
                                </Link>
                            </SpectrumLink>
                        </Flex>
                    ) : (
                        <Flex UNSAFE_className={`${classes.sidebarFooter} ${classes.mobile}`}>
                            <Link
                                to={paths.organization.about({ organizationId })}
                                viewTransition
                                className={classes.footerLink}
                            >
                                <Policy width={18} height={18} aria-label='Terms of use' />
                            </Link>
                        </Flex>
                    )}
                </Flex>
            </Flex>
        </Flex>
    );
};
