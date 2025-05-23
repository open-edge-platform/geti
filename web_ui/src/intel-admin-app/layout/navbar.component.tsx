// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';
import { NavLink } from 'react-router-dom';

import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';

import classes from './layout.module.scss';

interface NavbarItem {
    to: string;
    name: string;
}

export const Navbar = (): JSX.Element => {
    const { FEATURE_FLAG_MANAGE_USERS } = useFeatureFlags();

    const navbarItems: NavbarItem[] = FEATURE_FLAG_MANAGE_USERS
        ? [
              { to: paths.intelAdmin.organizations({}), name: 'Organizations' },
              { to: paths.intelAdmin.users({}), name: 'Users' },
          ]
        : [{ to: paths.intelAdmin.organizations({}), name: 'Organizations' }];

    return (
        <nav className={classes.navbarContainer}>
            <ul className={classes.navbarList}>
                {navbarItems.map(({ to, name }) => (
                    <li key={name} className={classes.navbarItem}>
                        <NavLink
                            to={to}
                            className={({ isActive }) =>
                                [classes.navbarLinkItem, isActive ? classes.navbarLinkItemActive : ''].join(' ')
                            }
                            viewTransition
                        >
                            {name}
                        </NavLink>
                    </li>
                ))}
            </ul>
        </nav>
    );
};
