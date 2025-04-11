// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Fragment } from 'react';

import { Text } from '@adobe/react-spectrum';
import clsx from 'clsx';
import { NavLink } from 'react-router-dom';

import { MenuOption } from '../menu-option.interface';

import classes from './sidebar-menu.module.scss';

interface SidebarMenuProps {
    id?: string;
    options: MenuOption[][];
    className?: React.HTMLAttributes<HTMLElement>['className'];
}

export const SidebarMenu = ({ id, options, className }: SidebarMenuProps): JSX.Element => {
    return (
        <nav className={className} id={`sidebar-menu-${id}`}>
            {options.map((optionsChildren, index) => (
                <Fragment key={index}>
                    <ul aria-label='list group' className={classes.linkGroup}>
                        {optionsChildren
                            .filter((option) => !option.isHidden)
                            .map((option) => (
                                <li key={option.id} aria-label={option.ariaLabel}>
                                    <NavLink
                                        to={option.url}
                                        className={(props) =>
                                            clsx(
                                                classes.link,
                                                props.isActive ? classes.activeLink : '',
                                                'icon' in option ? classes.linkHideable : ''
                                            )
                                        }
                                        viewTransition
                                    >
                                        {'icon' in option && option.icon}

                                        <Text
                                            id={`sidebar-menu-${option.id}`}
                                            marginY={'auto'}
                                            UNSAFE_className={clsx(
                                                classes.linkText,
                                                'icon' in option ? classes.linkTextHideable : ''
                                            )}
                                        >
                                            {option.name}
                                        </Text>
                                    </NavLink>
                                </li>
                            ))}
                    </ul>

                    {index + 1 < options.length && <div role='separator' className={classes.separator} />}
                </Fragment>
            ))}
        </nav>
    );
};
