// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createContext, ReactNode, useContext, useMemo, useState } from 'react';

interface AnnotationVisibilityState {
    isVisible: boolean;
    toggleVisibility: () => void;
    isFocussed: boolean;
    toggleFocus: () => void;
}

const VisibilityContext = createContext<AnnotationVisibilityState | null>(null);

export const AnnotationVisibilityProvider = ({ children }: { children: ReactNode }) => {
    const [isVisible, setIsVisible] = useState(true);
    const [isFocussed, setIsFocussed] = useState(false);

    const value = useMemo(
        () => ({
            isVisible,
            toggleVisibility: () => setIsVisible((prev) => !prev),
            isFocussed,
            toggleFocus: () => setIsFocussed((prev) => !prev),
        }),
        [isVisible, isFocussed]
    );

    return <VisibilityContext.Provider value={value}>{children}</VisibilityContext.Provider>;
};

export const useAnnotationVisibility = () => {
    const context = useContext(VisibilityContext);

    if (context === null) {
        throw new Error('useAnnotationVisibility must be used within AnnotationVisibilityProvider');
    }

    return context;
};
