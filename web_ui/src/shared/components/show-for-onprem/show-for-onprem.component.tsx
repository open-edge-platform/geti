// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';

interface ShowForOnPremProps {
    children: ReactNode;
}

export const ShowForOnPrem = ({ children }: ShowForOnPremProps): JSX.Element => {
    const isSaasEnv = useIsSaasEnv();

    if (isSaasEnv) {
        return <></>;
    }

    return <>{children}</>;
};
