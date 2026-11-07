// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface AddSinkProps {
    onSaved: () => void;
}

export interface EditSinkProps<T> {
    sink: T;
    isConnected: boolean;
    onSaved: () => void;
    onBackToList: () => void;
}
