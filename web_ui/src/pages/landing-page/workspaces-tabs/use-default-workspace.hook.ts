// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { WorkspaceEntity } from '@geti/core/src/workspaces/services/workspaces.interface';
import { isEmpty } from 'lodash-es';

import { WORKSPACES_SETTINGS_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../core/user-settings/hooks/use-global-settings.hook';
import { getSettingsOfType } from '../../../core/user-settings/utils';
import { hasDifferentId, hasEqualId } from '../../../shared/utils';

interface UseDefaultWorkspace {
    reorderedWorkspaces: WorkspaceEntity[];
    defaultWorkspaceId: string | undefined;
}

export const useDefaultWorkspace = (workspaces: WorkspaceEntity[]): UseDefaultWorkspace => {
    const settings = useUserGlobalSettings();

    const workspaceConfig = useMemo(
        () =>
            getSettingsOfType(settings.config, {
                ...WORKSPACES_SETTINGS_KEYS,
            }),
        [settings.config]
    );
    const defaultWorkspaceId = workspaceConfig.defaultWorkspace?.id;

    const defaultWorkspace = defaultWorkspaceId ? workspaces.find(hasEqualId(defaultWorkspaceId)) : undefined;
    const reorderedWorkspaces = !isEmpty(defaultWorkspace)
        ? [defaultWorkspace, ...workspaces.filter(hasDifferentId(defaultWorkspaceId))]
        : workspaces;

    return {
        reorderedWorkspaces,
        defaultWorkspaceId,
    };
};
