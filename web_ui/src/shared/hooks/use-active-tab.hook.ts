// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
