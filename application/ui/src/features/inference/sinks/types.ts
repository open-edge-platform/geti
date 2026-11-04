// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { RosSinkConfig, SinkConfig } from '@/api/types';

export type SupportedSinkConfig = Exclude<SinkConfig, RosSinkConfig>;

export interface AddSinkProps {
    onSaved: () => void;
}

export interface EditSinkProps<T> {
    sink: T;
    isConnected: boolean;
    onSaved: () => void;
    onBackToList: () => void;
}
