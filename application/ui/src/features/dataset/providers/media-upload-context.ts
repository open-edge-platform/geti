// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createContext, Dispatch, useContext } from 'react';

import type { Action, MediaUploadState } from './media-upload-reducer';

// State and dispatch are kept apart so components that only trigger uploads (the gallery, the
// toolbar) do not re-render once per uploaded file.
export const MediaUploadStateContext = createContext<MediaUploadState | null>(null);
export const MediaUploadDispatchContext = createContext<Dispatch<Action> | null>(null);
export const IsUploadingContext = createContext<boolean | null>(null);

export const useMediaUploadState = (): MediaUploadState => {
    const context = useContext(MediaUploadStateContext);

    if (context === null) {
        throw new Error('useMediaUploadState was used outside of MediaUploadProvider');
    }

    return context;
};

export const useMediaUploadDispatch = (): Dispatch<Action> => {
    const context = useContext(MediaUploadDispatchContext);

    if (context === null) {
        throw new Error('useMediaUploadDispatch was used outside of MediaUploadProvider');
    }

    return context;
};

export const useIsUploading = (): boolean => {
    const context = useContext(IsUploadingContext);

    if (context === null) {
        throw new Error('useIsUploading was used outside of MediaUploadProvider');
    }

    return context;
};
