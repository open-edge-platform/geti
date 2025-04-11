// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ProjectIdentifier } from '../../projects/core.interface';
import {
    AnnotatorSettingsConfig,
    CanvasSettingsConfig,
    FuxNotificationsConfig,
    FuxSettingsConfig,
    GeneralSettingsConfig,
    GlobalModalsConfig,
    TutorialConfig,
} from '../dtos/user-settings.interface';

export type UserGlobalSettings =
    | GlobalModalsConfig
    | GeneralSettingsConfig
    | TutorialConfig
    | FuxNotificationsConfig
    | FuxSettingsConfig;

export type UserProjectSettings = AnnotatorSettingsConfig & CanvasSettingsConfig;

export interface UseSettings<T extends UserGlobalSettings | UserProjectSettings> {
    saveConfig: (settings: T, successMessage?: string) => Promise<void>;
    isSavingConfig: boolean;
    config: T;
}

export interface UserSettingsService {
    getGlobalSettings: () => Promise<UserGlobalSettings>;
    getProjectSettings: (projectIdentifier: ProjectIdentifier) => Promise<UserProjectSettings>;
    saveGlobalSettings: (settings: UserGlobalSettings) => Promise<void>;
    saveProjectSettings: (projectIdentifier: ProjectIdentifier, settings: UserProjectSettings) => Promise<void>;
}
