// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, FC, useState } from 'react';

import {
    Button,
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    dimensionValue,
    Divider,
    Flex,
    Heading,
    Text,
    useMediaQuery,
    View,
} from '@geti/ui';
import { InfoOutline } from '@geti/ui/icons';
import { OverlayTriggerState } from '@react-stately/overlays';
import { isEmpty } from 'lodash-es';
import { useNavigate } from 'react-router-dom';

import { isLargeSizeQuery } from '../../../packages/ui/theme/queries';
import { DOMAIN } from '../../core/projects/core.interface';
import { useProjectActions } from '../../core/projects/hooks/use-project-actions.hook';
import { paths } from '../../core/services/routes';
import { useWorkspaceIdentifier } from '../../providers/workspaces-provider/use-workspace-identifier.hook';
import { TooltipWithDisableButton } from '../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { InfoSection } from './components/info-section/info-section.component';
import { getStepInfo, getTotalSteps } from './components/utils';
import { CreateProjectButton } from './create-project-button/create-project-button.component';
import {
    NewProjectDialogProvider,
    useNewProjectDialog,
} from './new-project-dialog-provider/new-project-dialog-provider.component';
import { STEPS } from './new-project-dialog-provider/new-project-dialog-provider.interface';
import { getLabelsNamesErrors, MIN_NUMBER_OF_LABELS_FOR_CLASSIFICATION } from './utils';

import classes from './new-project-dialog.module.scss';

interface NewProjectDialogProps {
    buttonText: string;
    openImportDatasetDialog: OverlayTriggerState;
}

const paddingStyle = {
    '--spectrum-dialog-padding-x': dimensionValue('size-500'),
    '--spectrum-dialog-padding-y': dimensionValue('size-500'),
} as CSSProperties;
const tabletPaddingStyle = {
    '--spectrum-dialog-padding-x': dimensionValue('size-300'),
    '--spectrum-dialog-padding-y': dimensionValue('size-300'),
} as CSSProperties;

interface NewProjectDialogInnerProps {
    onCloseDialog: () => void;
}

const NewProjectDialogInner: FC<NewProjectDialogInnerProps> = ({ onCloseDialog }) => {
    const { workspaceId, organizationId } = useWorkspaceIdentifier();
    const navigate = useNavigate();
    const { createProjectMutation } = useProjectActions();
    const isLargeSize = useMediaQuery(isLargeSizeQuery);

    const { content, hasNextStep, hasPreviousStep, goToNextStep, goToPreviousStep, validationError, metadata } =
        useNewProjectDialog();
    const { name, selectedDomains, projectTypeMetadata } = metadata;

    // Content (<ProjectLabelsManagement />) gets the correct "selectedDomain" as props
    const isClassificationDomain = content.props.selectedDomain === DOMAIN.CLASSIFICATION;
    const isPoseTemplate = metadata.currentStep === STEPS.POSE_TEMPLATE;

    const showClassificationInfo = isClassificationDomain && !hasNextStep;

    const pointNames = projectTypeMetadata.at(0)?.keypointStructure?.positions ?? [];
    const hasKeypointErrors = isPoseTemplate ? getLabelsNamesErrors(pointNames.map(({ label }) => label)) : undefined;

    const isCreationEnabled = isEmpty(validationError?.tree) && !validationError?.labels && isEmpty(hasKeypointErrors);

    const handleCreateProject = (): void => {
        createProjectMutation.mutate(
            {
                workspaceIdentifier: { workspaceId, organizationId },
                name,
                domains: selectedDomains,
                projectTypeMetadata,
            },
            {
                onSuccess: ({ id }) => {
                    onCloseDialog();

                    navigate(paths.project.index({ organizationId, workspaceId, projectId: id }));
                },
            }
        );
    };

    const stepInfo = getStepInfo(metadata.currentStep);
    const numberOfSteps = getTotalSteps(metadata);

    return (
        <Dialog
            height='100%'
            minWidth={{ base: 'auto', L: '90rem' }}
            UNSAFE_style={isLargeSize ? paddingStyle : tabletPaddingStyle}
        >
            <Heading id={`${metadata.currentStep}-title-id`}>
                <Flex direction={'column'} marginBottom={'size-250'}>
                    <Text>{stepInfo.title}</Text>
                    <Flex UNSAFE_className={classes.createProject} justifyContent={'space-between'}>
                        <Text>Create project</Text>
                        <Text>
                            {stepInfo.number} of {numberOfSteps}
                        </Text>
                    </Flex>
                </Flex>
            </Heading>
            <Divider />
            <Content UNSAFE_style={{ overflowX: 'hidden' }}>
                {content}
                {(metadata.currentStep === 'name-project' || metadata.currentStep === 'select-template') && (
                    <Divider size='S' />
                )}
            </Content>

            <ButtonGroup UNSAFE_style={{ paddingTop: 'size-300' }}>
                <View UNSAFE_style={{ position: 'absolute', left: 0, top: 0 }}>
                    {showClassificationInfo ? (
                        <InfoSection
                            icon={<InfoOutline />}
                            message={`Classification projects require at least
                                        ${MIN_NUMBER_OF_LABELS_FOR_CLASSIFICATION} top level labels.`}
                        />
                    ) : null}
                </View>
                <Button variant='secondary' onPress={onCloseDialog} id='cancel-new-project-button'>
                    Cancel
                </Button>

                {hasPreviousStep && (
                    <Button id='back-new-project-button' variant='secondary' onPress={goToPreviousStep}>
                        Back
                    </Button>
                )}
                {hasNextStep && (
                    <TooltipWithDisableButton placement={'top'} disabledTooltip={validationError?.tree}>
                        <Button
                            marginStart='size-200'
                            id='next-new-project-button'
                            variant='primary'
                            isDisabled={!isEmpty(validationError?.tree)}
                            onPress={goToNextStep}
                        >
                            Next
                        </Button>
                    </TooltipWithDisableButton>
                )}
                {!hasNextStep && (
                    <TooltipWithDisableButton
                        placement={'top'}
                        disabledTooltip={validationError?.tree || hasKeypointErrors}
                    >
                        <Button
                            id='confirm-create-new-project-button'
                            type='submit'
                            variant='accent'
                            position='relative'
                            marginStart='size-200'
                            onPress={handleCreateProject}
                            isPending={createProjectMutation.isPending}
                            isDisabled={!isCreationEnabled}
                        >
                            Create
                        </Button>
                    </TooltipWithDisableButton>
                )}
            </ButtonGroup>
        </Dialog>
    );
};

export const NewProjectDialog = ({ buttonText, openImportDatasetDialog }: NewProjectDialogProps): JSX.Element => {
    const [isOpen, setIsOpen] = useState<boolean>(false);

    const handleOpenDialog = (): void => {
        setIsOpen(true);
    };

    const handleCloseDialog = (): void => {
        setIsOpen(false);
    };

    return (
        <>
            <CreateProjectButton
                buttonText={buttonText}
                handleOpenDialog={handleOpenDialog}
                openImportDatasetDialog={openImportDatasetDialog}
            />

            <DialogContainer onDismiss={handleCloseDialog}>
                {isOpen && (
                    <NewProjectDialogProvider>
                        <NewProjectDialogInner onCloseDialog={handleCloseDialog} />{' '}
                    </NewProjectDialogProvider>
                )}
            </DialogContainer>
        </>
    );
};
