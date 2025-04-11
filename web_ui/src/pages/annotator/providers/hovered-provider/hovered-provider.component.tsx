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

import { createContext, ReactNode, useContext, useState } from 'react';

import noop from 'lodash/noop';

const HoveredIdContext = createContext<{
    hoveredId: string | null;
    setHoveredId: (id: string | null) => void;
}>({
    hoveredId: null,
    setHoveredId: noop,
});

export const HoveredProvider = ({
    children,
    hoveredId: defaultHoveredId = null,
}: {
    children: ReactNode;
    hoveredId?: string | null;
}) => {
    const [hoveredId, setHoveredId] = useState<string | null>(defaultHoveredId);

    return <HoveredIdContext.Provider value={{ hoveredId, setHoveredId }}>{children}</HoveredIdContext.Provider>;
};

const useHoveredId = (): string | null => {
    return useContext(HoveredIdContext).hoveredId;
};

export const useSetHoveredId = () => {
    return useContext(HoveredIdContext).setHoveredId;
};

export const useIsHovered = (id: string) => {
    const hoveredId = useHoveredId();
    return id === hoveredId;
};
