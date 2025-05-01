// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ButtonWithSpectrumTooltip } from '@shared/components/button-with-tooltip/button-with-tooltip.component';

import { GraphChart, List } from '../../../../assets/icons';

interface ProjectStorageToggleButtonProps {
    onPress: () => void;
    isProjectsListViewVisible: boolean;
}

export const ProjectStorageToggleButton = ({
    onPress,
    isProjectsListViewVisible,
}: ProjectStorageToggleButtonProps): JSX.Element => {
    return (
        <ButtonWithSpectrumTooltip
            isQuiet
            isClickable
            onPress={onPress}
            aria-label={`Switch to ${isProjectsListViewVisible ? 'graph' : 'table'} view`}
            tooltip={`Switch to ${isProjectsListViewVisible ? 'graph' : 'table'} view`}
        >
            {isProjectsListViewVisible ? <List /> : <GraphChart />}
        </ButtonWithSpectrumTooltip>
    );
};
