// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
    createContext,
    useContext,
    useMemo,
    useState,
    type Dispatch,
    type ReactNode,
    type SetStateAction,
} from 'react';

import type { Media } from '@/api/types';

import { isVideoFrame } from '../../../shared/media-item-utils';

export const annotationMediaKey = (projectId: string, media: Media) =>
    `${projectId}/${media.id}/${isVideoFrame(media) ? media.frame_number : 'image'}`;

interface AnnotationReviewContext {
    panelHost: HTMLDivElement | null;
    setPanelHost: Dispatch<SetStateAction<HTMLDivElement | null>>;
}
const ReviewContext = createContext<AnnotationReviewContext | null>(null);

/** Hosts the assistant beside the image without covering the editable canvas. */
export const AnnotationReviewProvider = ({ children }: { children: ReactNode }) => {
    const [panelHost, setPanelHost] = useState<HTMLDivElement | null>(null);
    const value = useMemo(() => ({ panelHost, setPanelHost }), [panelHost]);
    return <ReviewContext.Provider value={value}>{children}</ReviewContext.Provider>;
};

export const useAnnotationReview = () => useContext(ReviewContext);
