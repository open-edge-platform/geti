// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createContext, ReactNode, RefObject, use, useMemo, useRef } from 'react';

type AnnotatorContextProps = {
    canvasRef: RefObject<HTMLDivElement | null>;
};

const AnnotatorContext = createContext<AnnotatorContextProps | null>(null);

type AnnotatorProviderProps = {
    children: ReactNode;
};

export const AnnotatorProvider = ({ children }: AnnotatorProviderProps) => {
    const canvasRef = useRef<HTMLDivElement | null>(null);
    const value = useMemo(() => ({ canvasRef }), []);

    return <AnnotatorContext value={value}>{children}</AnnotatorContext>;
};

export const useAnnotator = () => {
    const context = use(AnnotatorContext);

    if (context === null) {
        throw new Error('useAnnotator must be used within an AnnotatorProvider');
    }

    return context;
};
