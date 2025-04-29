// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Heading, Image, Text } from '@adobe/react-spectrum';
import { View } from '@react-spectrum/view';
import { OverlayTriggerState } from '@react-stately/overlays';

import NoProjectsPlaceholder from '../../../../../assets/images/no-projects-placeholder.webp';
import { CustomWell } from '../../../../../shared/components/custom-well/custom-well.component';
import { HasPermission } from '../../../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../../../shared/components/has-permission/has-permission.interface';
import { NewProjectDialog } from '../../../../create-project/new-project-dialog.component';
import { LearnSectionCard } from './learn-section-card.component';

import workspaceClasses from '../../landing-page-workspace.module.scss';
import classes from './no-project-area.module.scss';

interface NoProjectsAreaProps {
    openImportDatasetDialog: OverlayTriggerState;
}

export const NoProjectArea = ({ openImportDatasetDialog }: NoProjectsAreaProps): JSX.Element => {
    const TITLE = 'Create your first project';
    const DESCRIPTION = 'Create new project to leverage AI to automate your Computer Vision task';

    return (
        <Flex width={'100%'} gap={'size-300'}>
            <CustomWell
                height={'size-3400'}
                minWidth={'size-3000'}
                margin={0}
                id='no-project-area'
                data-testid={'no-project-area'}
                isSelectable={false}
                flex={'1'}
            >
                <Flex height={'100%'}>
                    <Image
                        src={NoProjectsPlaceholder}
                        alt={''}
                        minHeight={'100%'}
                        objectFit={'cover'}
                        UNSAFE_className={workspaceClasses.image}
                    />
                    <Flex
                        direction={'column'}
                        marginTop={'size-300'}
                        marginStart={'size-300'}
                        marginEnd={'size-700'}
                        justifyContent={'space-between'}
                    >
                        <View UNSAFE_className={classes.description}>
                            <Heading id={'no-projects-area-title'} level={3} margin={0}>
                                {TITLE}
                            </Heading>
                            <Text id={'no-projects-area-description'}>{DESCRIPTION}</Text>
                        </View>
                        <View marginBottom={'size-300'}>
                            <HasPermission operations={[OPERATION.PROJECT_CREATION]}>
                                <NewProjectDialog
                                    buttonText={'Create new project'}
                                    openImportDatasetDialog={openImportDatasetDialog}
                                />
                            </HasPermission>
                        </View>
                    </Flex>
                </Flex>
            </CustomWell>

            <LearnSectionCard />
        </Flex>
    );
};
