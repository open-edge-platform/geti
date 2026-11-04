// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface AddSourceProps {
    existingNames: string[];
    onSaved: () => void;
}

export interface EditSourceProps<T> {
    source: T;
    isConnected: boolean;
    onSaved: () => void;
    onBackToList: () => void;
}
