// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { NavLink } from 'react-router-dom';

import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';
import { paths } from '../../core/services/routes';

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
