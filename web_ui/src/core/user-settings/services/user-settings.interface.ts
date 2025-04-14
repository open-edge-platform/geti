// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
