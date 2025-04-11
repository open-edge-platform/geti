// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect } from 'react';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { isClassificationDomain } from '../../../../core/projects/domains';
import { Task } from '../../../../core/projects/task.interface';
import { FEATURES_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { UserProjectSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { getSettingsOfType } from '../../../../core/user-settings/utils';
import { getPanelSettingsKey } from '../../../../shared/local-storage-keys';
import { getParsedLocalStorage } from '../../../../shared/utils';
import { containsFeatureConfig } from '../../components/navigation-toolbar/settings/utils';

export const usePanelsConfig = (
    selectedTask: Task | null,
    tasks: Task[],
    settings: UseSettings<UserProjectSettings>,
    projectId: string
) => {
    // Disable annotation panel by default for classification and anomaly classification projects
    useEffect(() => {
        const isAnnotatorSettingUpdated = getParsedLocalStorage<boolean>(getPanelSettingsKey(projectId)) ?? false;

        const isSegmentationInstance = selectedTask?.domain === DOMAIN.SEGMENTATION_INSTANCE;

        const isSingleClassificationTask =
            tasks.length === 1 && selectedTask !== null && isClassificationDomain(selectedTask.domain);

        const annotatorPanelIsEnabled =
            containsFeatureConfig(settings.config) && settings.config[FEATURES_KEYS.ANNOTATION_PANEL].isEnabled;

        const isClassificationAnnotatorPanel =
            isSingleClassificationTask && annotatorPanelIsEnabled && !isAnnotatorSettingUpdated;

        const countingPanelIsNotEnabled =
            containsFeatureConfig(settings.config) && !settings.config[FEATURES_KEYS.COUNTING_PANEL].isEnabled;

        const isSegmentationCountingPanel =
            isSegmentationInstance && countingPanelIsNotEnabled && !isAnnotatorSettingUpdated;

        const config = getSettingsOfType(settings.config, FEATURES_KEYS);
        const newAnnotationPanelConfig = isClassificationAnnotatorPanel
            ? {
                  [FEATURES_KEYS.ANNOTATION_PANEL]: { ...config[FEATURES_KEYS.ANNOTATION_PANEL], isEnabled: false },
              }
            : {};

        const newCountingPanelConfig = isSegmentationCountingPanel
            ? {
                  [FEATURES_KEYS.COUNTING_PANEL]: { ...config[FEATURES_KEYS.COUNTING_PANEL], isEnabled: true },
              }
            : {};

        if (isClassificationAnnotatorPanel || isSegmentationCountingPanel) {
            settings.saveConfig({
                ...settings.config,
                ...newAnnotationPanelConfig,
                ...newCountingPanelConfig,
            });
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedTask]);
};
