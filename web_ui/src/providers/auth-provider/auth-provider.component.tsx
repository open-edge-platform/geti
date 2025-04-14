// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { AuthProviderProps, AuthProvider as OIDCProvider } from 'react-oidc-context';

import { useOIDCConfiguration } from '../../core/auth/use-oidc-configuration.hook';

export const AuthProvider = ({
    children,
    isAdmin = false,
}: {
    children: ReactNode;
    configuration?: AuthProviderProps;
    isAdmin?: boolean;
}) => {
    const configuration = useOIDCConfiguration(isAdmin);

    return <OIDCProvider {...configuration}>{children}</OIDCProvider>;
};
