// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useEffect, useMemo, useState } from 'react';

import {
    ActionButton,
    Button,
    ButtonGroup,
    Content,
    Dialog,
    DialogTrigger,
    Divider,
    Heading,
    Item,
    TabList,
    TabPanels,
    Tabs,
    Tooltip,
    TooltipTrigger,
} from '@geti/ui';
import { Gear } from '@geti/ui/icons';
import { isEqual, isNil } from 'lodash-es';
import { useLocalStorage } from 'usehooks-ts';

import { isClassificationDomain } from '../../../../../core/projects/domains';
import {
    AnnotatorSettingsConfig,
    FEATURES_KEYS,
    SettingsKeys,
} from '../../../../../core/user-settings/dtos/user-settings.interface';
import { UserProjectSettings, UseSettings } from '../../../../../core/user-settings/services/user-settings.interface';
import { getSettingsOfType } from '../../../../../core/user-settings/utils';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { getPanelSettingsKey } from '../../../../../shared/local-storage-keys';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { ActiveLearningSettings } from './active-learning-settings.component';
import { AnnotatorSectionSettings } from './annotator-section-settings.component';
import { containsFeatureConfig } from './utils';

import classes from './settings.module.scss';

interface TabProps {
    id: string;
    children: ReactNode;
    name: string;
}

interface SettingsProps {
    settings: UseSettings<UserProjectSettings>;
    isDarkMode?: boolean;
}

export const Settings = ({ settings, isDarkMode = false }: SettingsProps): JSX.Element => {
    const { saveConfig, isSavingConfig } = settings;
    const { selectedTask, tasks } = useTask();
    const { projectId } = useProjectIdentifier();
    const [, setLsSettingFlag] = useLocalStorage<boolean>(getPanelSettingsKey(projectId), false);
    const isSingleClassification =
        tasks.length === 1 && !isNil(selectedTask) && isClassificationDomain(selectedTask.domain);

    const config = useMemo(
        () =>
            getSettingsOfType(settings.config, {
                ...FEATURES_KEYS,
            }),
        [settings.config]
    ) as AnnotatorSettingsConfig;

    // Used for temporary state before the user saves the changes
    const [tempConfig, setTempConfig] = useState<AnnotatorSettingsConfig>(config);
    const hasUnsavedChanges = !isEqual(tempConfig, config);

    useEffect(() => {
        setTempConfig(config);
    }, [config]);

    const handleToggleFeature = (isEnabled: boolean, feature: SettingsKeys) => {
        setTempConfig((prevConfig) => {
            if (containsFeatureConfig(prevConfig)) {
                return {
                    ...prevConfig,
                    [feature]: { ...prevConfig[feature as FEATURES_KEYS], isEnabled },
                };
            }

            return prevConfig;
        });
    };

    const tabs = [
        {
            id: 'annotator-settings-tab',
            name: 'Annotator sections',
            children: (
                <AnnotatorSectionSettings
                    config={tempConfig}
                    isSingleClassification={isSingleClassification}
                    handleToggleFeature={handleToggleFeature}
                />
            ),
        },
        {
            id: 'active-learning-settings-tab',
            name: 'Active learning',
            children: <ActiveLearningSettings config={tempConfig} handleToggleFeature={handleToggleFeature} />,
        },
    ];

    return (
        <DialogTrigger>
            <TooltipTrigger placement={'bottom'}>
                <ActionButton
                    isQuiet
                    colorVariant={isDarkMode ? 'dark' : 'light'}
                    aria-label='Settings'
                    data-testid='settings-icon'
                >
                    <Gear width={15} />
                </ActionButton>
                <Tooltip>Settings</Tooltip>
            </TooltipTrigger>

            {(close) => (
                <Dialog UNSAFE_className={classes.dialogWrapper}>
                    <Heading>Settings</Heading>

                    <Divider />

                    <Content UNSAFE_className={classes.dialogContent}>
                        <Tabs aria-label='Settings dialog' orientation='vertical' height={'100%'} items={tabs}>
                            <TabList UNSAFE_className={classes.tabList}>
                                {(item: TabProps) => <Item key={item.id}>{item.name}</Item>}
                            </TabList>
                            <TabPanels UNSAFE_className={classes.tabPanels}>
                                {(item: TabProps) => <Item key={item.id}>{item.children}</Item>}
                            </TabPanels>
                        </Tabs>
                    </Content>

                    <ButtonGroup>
                        <Button variant='secondary' onPress={close} data-testid='cancel-settings-dialog-id'>
                            Cancel
                        </Button>
                        <Button
                            onPress={() => {
                                saveConfig({ ...settings.config, ...tempConfig });
                                setLsSettingFlag(true);
                                close();
                            }}
                            isPending={isSavingConfig}
                            isDisabled={!hasUnsavedChanges}
                            aria-label={'Save settings'}
                            data-testid={'save-settings-dialog-id'}
                        >
                            Save
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogTrigger>
    );
};
