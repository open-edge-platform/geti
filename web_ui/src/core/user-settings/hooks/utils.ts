// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface SaveSettingsMutation<T> {
    settings: T;
    successMessage?: string;
}

export interface SaveSettingsMutationContext<T> {
    previousSettings: T | undefined;
}

export const SETTINGS_QUERY_STALE_TIME = 1000 * 60;
