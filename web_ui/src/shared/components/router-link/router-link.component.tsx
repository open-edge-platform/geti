// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps } from 'react';

import { Link } from '@adobe/react-spectrum';
import { Link as ReactRouterLink } from 'react-router-dom';

interface RouterLinkProps extends ComponentProps<typeof Link> {
    to: ComponentProps<typeof ReactRouterLink>['to'];
}

export const RouterLink = ({ children, to, ...rest }: RouterLinkProps): JSX.Element => {
    return (
        <Link UNSAFE_style={{ textDecoration: 'none', color: 'currentColor' }} {...rest}>
            <ReactRouterLink to={to} viewTransition>
                {children}
            </ReactRouterLink>
        </Link>
    );
};
