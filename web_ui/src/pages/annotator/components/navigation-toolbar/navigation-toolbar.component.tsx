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

import { Flex, Grid, minmax, Text, View } from '@adobe/react-spectrum';
import { useMediaQuery } from '@react-spectrum/utils';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { isAnomalyDomain, isClassificationDomain } from '../../../../core/projects/domains';
import { FUX_NOTIFICATION_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { UserProjectSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { CoachMark } from '../../../../shared/components/coach-mark/coach-mark.component';
import { AutoTrainingCoachMark } from '../../../../shared/components/coach-mark/fux-notifications/auto-training-coach-mark.component';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { DomainName } from '../../../../shared/components/domain-name/domain-name.component';
import { ActiveLearningConfiguration } from '../../../../shared/components/header/active-learning-configuration/active-learning-configuration.component';
import { CreditBalanceStatus } from '../../../../shared/components/header/credit-balance/credit-balance-status.component';
import { JobsActionIcon } from '../../../../shared/components/header/jobs-management/jobs-action-icon.component';
import { useIsCreditAccountEnabled } from '../../../../shared/hooks/use-is-credit-account-enabled';
import { hasEqualSize } from '../../../../shared/utils';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { useSelectedDataset } from '../../../project-details/components/project-dataset/use-selected-dataset/use-selected-dataset.hook';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useRequiredAnnotations } from '../../hooks/use-required-annotations.hook';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { AnnotationPredictionToggle } from './annotation-prediction-toggle.component';
import { AnnotationsRequired } from './annotations-required/annotations-required.component';
import { DefaultLabelCombobox } from './default-label-combobox.component';
import { NavigationBreadcrumbs } from './navigation-breadcrumbs/navigation-breadcrumbs.component';
import { ProjectPerformance } from './project-performance.component';
import { Settings } from './settings/settings.component';

import classes from './navigation-toolbar.module.scss';

export const NavigationToolbar = ({ settings }: { settings: UseSettings<UserProjectSettings> }): JSX.Element => {
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const selectedDataset = useSelectedDataset();
    const isCreditAccountEnabled = useIsCreditAccountEnabled();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();

    const { activeDomains, setDefaultLabel, defaultLabel, selectedTask } = useTask();
    const { project, projectIdentifier, isSingleDomainProject, isTaskChainProject } = useProject();

    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);

    // Required annotations should not be shown for anomaly projects or testing datasets
    const hideRequiredAnnotations = !selectedDataset.useForTraining;
    const hideDefaultLabelCombobox = hasEqualSize(activeDomains.filter(isClassificationDomain), activeDomains);
    const isAutoTrainingVisible = !isAnomalyProject;
    const requiredAnnotations = useRequiredAnnotations(selectedTask);
    const numberOfRequiredAnnotations = requiredAnnotations.reduce((all, currentTask) => all + currentTask.value, 0);
    const customMessageFirstAnnotation =
        `You have annotated your first image.\nAnnotate ${numberOfRequiredAnnotations}` +
        ` more to start the first auto-training job.`;

    return (
        <View backgroundColor='gray-200' gridArea='navigationToolbar' padding='size-100' id={'annotator-header'}>
            <Grid columns={['3fr', 'auto']}>
                <Grid
                    gap='size-100'
                    marginEnd='size-100'
                    justifyItems='center'
                    columns={{
                        base: [minmax('min-content', 'size-1600'), '1fr', 'min-content'],
                        L: [minmax('min-content', 'size-2400'), '1fr', 'min-content'],
                    }}
                >
                    <View justifySelf='flex-start'>
                        {hideDefaultLabelCombobox ? (
                            <></>
                        ) : (
                            <DefaultLabelCombobox
                                key={selectedTask?.id}
                                defaultLabel={defaultLabel}
                                setDefaultLabel={setDefaultLabel}
                            />
                        )}
                    </View>
                    {isTaskChainProject && <NavigationBreadcrumbs />}

                    {!isTaskChainProject && isLargeSize && (
                        <Flex
                            justifyContent={'center'}
                            alignItems={'center'}
                            data-testid={'project-name-domain-id'}
                            width={'100%'}
                            minWidth={0}
                        >
                            <Text UNSAFE_className={[classes.ellipsis, classes.noWrap].join(' ')}>{project.name}</Text>
                            <Text UNSAFE_className={classes.noWrap}>
                                @ {<DomainName domain={project.domains[0]} />}
                            </Text>
                        </Flex>
                    )}

                    <AnnotationPredictionToggle />
                </Grid>

                <View UNSAFE_className={isLargeSize ? classes.annotationsDetails : ''}>
                    <Flex justifyContent='space-between' alignItems='center' height='100%' gap='size-100'>
                        <Divider orientation='vertical' size='S' />

                        {hideRequiredAnnotations ? (
                            <View flexGrow={1} />
                        ) : (
                            <View>
                                <AnnotationsRequired
                                    selectedTask={selectedTask}
                                    id={'navigation-toolbar-required-annotations'}
                                    data-testid={'navigation-toolbar-required-annotations'}
                                />

                                <CoachMark
                                    settingsKey={FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING}
                                    customDescription={customMessageFirstAnnotation}
                                    styles={{
                                        position: 'absolute',
                                        top: '50px',
                                        right: FEATURE_FLAG_CREDIT_SYSTEM ? '221px' : '182px',
                                        zIndex: 99999,
                                    }}
                                />
                            </View>
                        )}

                        <Divider orientation='vertical' size='S' />

                        {isAutoTrainingVisible && (
                            <ActiveLearningConfiguration key={'auto-training'} isDarkMode selectedTask={selectedTask} />
                        )}

                        {isCreditAccountEnabled && <CreditBalanceStatus key='credit-balance-status' isDarkMode />}

                        <ProjectPerformance
                            key={'performance'}
                            performance={project.performance}
                            projectIdentifier={projectIdentifier}
                            isTaskChainProject={isTaskChainProject}
                        />

                        <View key='jobs'>
                            <JobsActionIcon isDarkMode />
                            <AutoTrainingCoachMark />
                        </View>

                        <Settings key='settings' isDarkMode settings={settings} />
                    </Flex>
                </View>
            </Grid>
        </View>
    );
};
