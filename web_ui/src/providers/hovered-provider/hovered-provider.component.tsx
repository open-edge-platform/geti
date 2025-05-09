// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext, useState } from 'react';

import { noop } from 'lodash-es';

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
