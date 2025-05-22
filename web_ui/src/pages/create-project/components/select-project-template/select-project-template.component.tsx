// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useEffect } from 'react';

import { dimensionValue, useMediaQuery } from '@geti/ui';
import { isLargeSizeQuery } from '@geti/ui/theme';
import { omit } from 'lodash-es';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { LabelTreeItem } from '../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { TaskMetadata } from '../../../../core/projects/task.interface';
import { SliderAnimation } from '../../../../shared/components/slider-animation/slider-animation.component';
import { Tabs } from '../../../../shared/components/tabs/tabs.component';
import { TabItem } from '../../../../shared/components/tabs/tabs.interface';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import {
    CreateNewProjectSelectedTabType,
    ProjectMetadata,
    ProjectType,
    SingleTaskTemplateType,
    STEPS,
} from '../../new-project-dialog-provider/new-project-dialog-provider.interface';
import { DomainCardsMetadata } from './project-template.interface';
import { SingleTaskTemplate } from './single-task-template.component';
import { TaskChainTemplate } from './task-chain-template.component';
import { TABS_SINGLE_TEMPLATE, taskChainSubDomains } from './utils';

import classes from './project-template.module.scss';

interface SelectProjectTemplateProps {
    animationDirection: number;
    metadata: ProjectMetadata;
    updateProjectState: (projectState: Partial<ProjectMetadata>) => void;
    setValidationError: (message?: string) => void;
}

const filterOutKeypointDetection = (tabs: Record<SingleTaskTemplateType, DomainCardsMetadata[]>, isFlagOn: boolean) =>
    isFlagOn ? tabs : omit(tabs, 'Keypoint Detection');

export const SelectProjectTemplate = ({
    animationDirection,
    metadata,
    updateProjectState,
    setValidationError,
}: SelectProjectTemplateProps): JSX.Element => {
    const { selectedDomains, selectedTab, projectTypeMetadata } = metadata;
    const { FEATURE_FLAG_ANOMALY_REDUCTION, FEATURE_FLAG_KEYPOINT_DETECTION } = useFeatureFlags();

    useEffect(() => {
        // Note: Need to reset validation error when coming back from labels step
        setValidationError(undefined);
    });

    const isLargeSize = useMediaQuery(isLargeSizeQuery);

    const setDomains = (newDomains: DOMAIN[], relations: LabelsRelationType[]): void => {
        const newProjectTypeMetadata: TaskMetadata[] = newDomains.map((domain, index) => {
            const domainTaskMetadata = projectTypeMetadata.find((taskMetadata) => taskMetadata.domain === domain);

            if (domainTaskMetadata && domainTaskMetadata.relation === relations[index]) {
                return domainTaskMetadata;
            } else {
                return { domain, relation: relations[index], labels: [] as LabelTreeItem[] } as TaskMetadata;
            }
        });

        updateProjectState({ selectedDomains: newDomains, projectTypeMetadata: newProjectTypeMetadata });
    };

    const handleTabSelectionChange = (inputKey: Key) => {
        const key = inputKey as CreateNewProjectSelectedTabType;

        updateProjectState({
            projectType: key === 'Chained tasks' ? ProjectType.TASK_CHAIN : ProjectType.SINGLE,
            selectedTab: key,
        });
    };

    const tabs = FEATURE_FLAG_ANOMALY_REDUCTION
        ? {
              ...filterOutKeypointDetection(TABS_SINGLE_TEMPLATE, FEATURE_FLAG_KEYPOINT_DETECTION),
              Anomaly: TABS_SINGLE_TEMPLATE.Anomaly.filter(
                  (template) => template.domain === DOMAIN.ANOMALY_CLASSIFICATION
              ),
          }
        : filterOutKeypointDetection(TABS_SINGLE_TEMPLATE, FEATURE_FLAG_KEYPOINT_DETECTION);

    const ITEMS: TabItem[] = [
        ...Object.entries(tabs).map(([tab, cards]) => ({
            id: `${idMatchingFormat(STEPS.SELECT_TEMPLATE)}-${idMatchingFormat(tab)}-id`,
            key: `${tab}`,
            name: tab,
            children: (
                <SingleTaskTemplate cards={cards} setSelectedDomains={setDomains} metaData={projectTypeMetadata[0]} />
            ),
        })),
        {
            id: `${idMatchingFormat(STEPS.SELECT_TEMPLATE)}-chain-id`,
            key: 'Chained tasks',
            name: 'Chained tasks',
            children: (
                <TaskChainTemplate
                    subDomains={taskChainSubDomains}
                    selectedDomains={selectedDomains}
                    setSelectedDomains={setDomains}
                />
            ),
        },
    ];

    return (
        <SliderAnimation animationDirection={animationDirection}>
            <Tabs
                items={ITEMS}
                aria-label='Templates types'
                selectedKey={selectedTab}
                width={{ base: 'auto', L: '816px' }}
                onSelectionChange={handleTabSelectionChange}
                tabStyles={{
                    padding: dimensionValue(isLargeSize ? 'size-300' : 'size-150'),
                    marginBottom: 'size-500',
                }}
                tabPanelsClassName={classes.templateProjectSelection}
            />
        </SliderAnimation>
    );
};
