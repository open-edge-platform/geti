// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Dispatch, SetStateAction, useEffect, useMemo, useState } from 'react';

import { Flex, View } from '@adobe/react-spectrum';
import { useMediaQuery } from '@react-spectrum/utils';

import { FEATURES_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { UserProjectSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { getSettingsOfType } from '../../../../core/user-settings/utils';
import { useViewMode } from '../../../../hooks/use-view-mode/use-view-mode.hook';
import { MEDIA_CONTENT_BUCKET } from '../../../../providers/media-upload-provider/media-upload.interface';
import { ActiveDatasetCoachMark } from '../../../../shared/components/coach-mark/fux-notifications/active-dataset-coach-mark.component';
import { INITIAL_VIEW_MODE } from '../../../../shared/components/media-view-modes/utils';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { ToolAnnotationContextProps } from '../../tools/tools.interface';
import { SidebarPanel } from './sidebar-panel.component';
import { SidebarSplitPanel } from './sidebar-split-panel.component';
import { SidebarCommonProps } from './sidebar.interface';
import { ToggleSidebarButton } from './toggle-sidebar-button.component';

interface SidebarProps extends ToolAnnotationContextProps {
    settings: UseSettings<UserProjectSettings>;
}

const useReopenSideBar = (isLargeSize: boolean): { isOpen: boolean; setIsOpen: Dispatch<SetStateAction<boolean>> } => {
    const [isOpen, setIsOpen] = useState(true);

    useEffect(() => {
        if (!isLargeSize && !isOpen) {
            setIsOpen(true);
        }
    }, [isLargeSize, isOpen, setIsOpen]);

    return { isOpen, setIsOpen };
};

export const Sidebar = ({ annotationToolContext, settings }: SidebarProps): JSX.Element => {
    const config = useMemo(() => getSettingsOfType(settings.config, FEATURES_KEYS), [settings.config]);
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const { selectedMediaItem } = useSelectedMediaItem();
    const { isOpen, setIsOpen } = useReopenSideBar(isLargeSize);
    const [datasetViewMode, setDatasetViewMode] = useViewMode(MEDIA_CONTENT_BUCKET.GENERIC, INITIAL_VIEW_MODE);

    const showDatasetPanel = config[FEATURES_KEYS.DATASET_PANEL].isEnabled;
    const showCountingPanel = config[FEATURES_KEYS.COUNTING_PANEL].isEnabled;
    const showAnnotationPanel = config[FEATURES_KEYS.ANNOTATION_PANEL].isEnabled;

    const sideBarProps: SidebarCommonProps = {
        showDatasetPanel,
        showCountingPanel,
        showAnnotationPanel,
        annotationToolContext,
        datasetViewMode,
        setDatasetViewMode,
    };

    return (
        <View gridArea='aside' backgroundColor='gray-200' zIndex={10}>
            <Flex gap='1px' direction='column' height='100%'>
                {isLargeSize && (
                    <ToggleSidebarButton aria-label='toggle sidebar' onChange={setIsOpen} isSelected={isOpen} />
                )}

                {isOpen && isLargeSize ? (
                    <SidebarSplitPanel selectedMediaItem={selectedMediaItem} {...sideBarProps} />
                ) : (
                    <SidebarPanel {...sideBarProps} />
                )}
            </Flex>
            <ActiveDatasetCoachMark />
        </View>
    );
};
