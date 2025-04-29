// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { useLocation } from 'react-router-dom';

const getActiveTab = (pathName: string): string | undefined => {
    const paths = pathName.split('/');
    const isRootPath = paths[paths.length - 1] === '';

    return isRootPath ? undefined : paths[paths.length - 1];
};

export const useActiveTab = (defaultKey: string) => {
    const location = useLocation();
    const [activeTab, setActiveTab] = useState<string>(() => getActiveTab(location.pathname) ?? defaultKey);

    useEffect(() => {
        const tab = getActiveTab(location.pathname);

        if (tab === activeTab) return;

        setActiveTab(tab ?? defaultKey);

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [location]);

    return activeTab;
};
