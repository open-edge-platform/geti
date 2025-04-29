// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
