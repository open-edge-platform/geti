// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createContext, ReactNode, useContext, useMemo, useState, type Dispatch, type SetStateAction } from 'react';

import type { Annotation } from '../../../shared/types';

type AnnotationsClipboard = {
    annotations: Annotation[];
    sourceMediaKey: string;
};

type PastedAnnotationGroup = {
    mediaKey: string;
    ids: string[];
};

type AnnotationsClipboardContextProps = {
    clipboard: AnnotationsClipboard | null;
    setClipboard: Dispatch<SetStateAction<AnnotationsClipboard | null>>;
    pastedAnnotationGroups: PastedAnnotationGroup[];
    setPastedAnnotationGroups: Dispatch<SetStateAction<PastedAnnotationGroup[]>>;
};

const AnnotationsClipboardContext = createContext<AnnotationsClipboardContextProps | null>(null);

export const AnnotationsClipboardProvider = ({ children }: { children: ReactNode }) => {
    const [clipboard, setClipboard] = useState<AnnotationsClipboard | null>(null);
    const [pastedAnnotationGroups, setPastedAnnotationGroups] = useState<PastedAnnotationGroup[]>([]);

    const value = useMemo(
        () => ({ clipboard, setClipboard, pastedAnnotationGroups, setPastedAnnotationGroups }),
        [clipboard, pastedAnnotationGroups]
    );

    return <AnnotationsClipboardContext value={value}>{children}</AnnotationsClipboardContext>;
};

export const useAnnotationsClipboard = () => {
    const context = useContext(AnnotationsClipboardContext);

    if (context === null) {
        throw new Error('useAnnotationsClipboard must be used within "AnnotationsClipboardProvider"');
    }

    return context;
};
