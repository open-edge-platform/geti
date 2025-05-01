// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Divider, Flex, Text, View } from '@adobe/react-spectrum';
import { CustomWellClickable } from '@shared/components/custom-well/custom-well-clickable.component';
import { DomainName } from '@shared/components/domain-name/domain-name.component';
import { TruncatedTextWithTooltip } from '@shared/components/truncated-text/truncated-text.component';
import { isNotCropDomain, openNewTab } from '@shared/utils';
import dayjs from 'dayjs';
import { Link, useNavigate } from 'react-router-dom';

import { Label as LabelInterface } from '../../../../../../../core/labels/label.interface';
import { getNonEmptyLabelsFromProject } from '../../../../../../../core/labels/utils';
import { DOMAIN, ProjectIdentifier } from '../../../../../../../core/projects/core.interface';
import { useExportProject } from '../../../../../../../core/projects/hooks/use-export-project.hook';
import { useProjectActions } from '../../../../../../../core/projects/hooks/use-project-actions.hook';
import { ProjectProps } from '../../../../../../../core/projects/project.interface';
import { paths } from '../../../../../../../core/services/routes';
import { useWorkspaceIdentifier } from '../../../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { idMatchingFormat } from '../../../../../../../test-utils/id-utils';
import { ProjectListItemSkeletonLoader } from '../project-list-item-skeleton-loader.component';
import { Label } from './components/label/label.component';
import { ProjectActionMenu } from './components/project-action-menu/project-action-menu.component';
import { ProjectExportStatus } from './project-export-status.component';
import { ProjectPerformance } from './project-performance.component';
import { ProjectThumbnail } from './project-thumbnail.component';

import classes from './project.module.scss';
import sharedClasses from '@shared/shared.module.scss';

export const Project = ({ project }: { project: ProjectProps }): JSX.Element => {
    const navigate = useNavigate();

    const { id, name, creationDate, thumbnail, tasks, domains, performance } = project;
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { exportProjectMutation } = useExportProject();
    const { deleteProjectMutation } = useProjectActions();

    const [isExporting, setIsExporting] = useState(false);

    const labels = getNonEmptyLabelsFromProject(tasks);
    const filteredDomains = domains.filter(isNotCropDomain);

    const exportProject = (projectIdentifier: ProjectIdentifier) => {
        exportProjectMutation.mutate(projectIdentifier, {
            onSuccess: () => {
                setIsExporting(true);
            },
        });
    };

    const deleteProject = (projectIdentifier: ProjectIdentifier, onSuccess: () => void) => {
        deleteProjectMutation.mutate(projectIdentifier, { onSuccess });
    };

    const handleOnPress = () => {
        navigate(paths.project.index({ organizationId, workspaceId, projectId: id }));
    };

    const handleMiddleClick = () => {
        openNewTab(paths.project.index({ organizationId, workspaceId, projectId: id }));
    };

    if (deleteProjectMutation.isPending) {
        return <ProjectListItemSkeletonLoader itemCount={1} style={{ marginTop: 0 }} />;
    }

    return (
        <CustomWellClickable
            id={`project-id-${id}`}
            onPress={handleOnPress}
            className={`${classes.wellClickable} ${sharedClasses.scaling}`}
            onAuxClick={handleMiddleClick}
        >
            <>
                <Flex height={'size-1700'}>
                    <View aria-label={'project thumbnail'} UNSAFE_className={classes.thumbnailWrapper}>
                        <Flex
                            width={'100%'}
                            height={'100%'}
                            alignItems={'center'}
                            justifyContent={'center'}
                            UNSAFE_style={{ overflow: 'hidden', borderRadius: 'inherit' }}
                        >
                            <ProjectThumbnail
                                alt={name}
                                thumbnail={thumbnail}
                                className={classes.thumbnail}
                                errorClassName={classes.icon}
                                id={`project-image-${idMatchingFormat(name)}`}
                            />
                        </Flex>
                    </View>

                    <Flex direction={'column'} minWidth={0} width={'100%'} marginTop={'size-200'} marginX={'size-200'}>
                        <Flex justifyContent={'space-between'} minWidth={0}>
                            <Link
                                to={paths.project.index({ organizationId, workspaceId, projectId: id })}
                                className={classes.projectNameLink}
                                viewTransition
                            >
                                <View minWidth={0} width={'100%'}>
                                    <Flex alignItems={'center'} wrap>
                                        <TruncatedTextWithTooltip
                                            id={`project-name-${idMatchingFormat(name)}`}
                                            UNSAFE_className={classes.projectName}
                                        >
                                            {project.name}
                                        </TruncatedTextWithTooltip>
                                        <Text marginStart={'size-50'} marginEnd={'size-25'}>
                                            @
                                        </Text>
                                        {filteredDomains.map((domain: DOMAIN, index: number) => {
                                            const shouldShowArrow = index < filteredDomains.length - 1;

                                            return (
                                                <Text key={domain} marginEnd={'size-25'}>
                                                    <DomainName domain={domain} />
                                                    {shouldShowArrow ? <Text marginX={'size-25'}>&#8594;</Text> : <></>}
                                                </Text>
                                            );
                                        })}
                                    </Flex>

                                    <Text
                                        UNSAFE_style={{ fontSize: 'var(--spectrum-global-dimension-font-size-75)' }}
                                        id={`project-date-${idMatchingFormat(name)}`}
                                    >
                                        Created: {dayjs(creationDate).format('D MMMM YYYY | h:mm A')}
                                    </Text>
                                </View>
                            </Link>

                            <Flex alignItems={'start'}>
                                <ProjectPerformance performance={performance} />
                                <ProjectActionMenu
                                    project={project}
                                    isExporting={isExporting}
                                    onExportProject={exportProject}
                                    onDeleteProject={deleteProject}
                                />
                            </Flex>
                        </Flex>

                        <Divider size='S' marginTop={'size-200'} />

                        <Flex UNSAFE_className={classes.projectLabels}>
                            {labels.map((label: LabelInterface) => (
                                <Label label={label} key={label.id} projectName={name} />
                            ))}
                        </Flex>
                    </Flex>
                </Flex>
                <ProjectExportStatus
                    projectId={id}
                    isExporting={isExporting}
                    setIsExporting={setIsExporting}
                    workspaceIdentifier={{ organizationId, workspaceId }}
                    exportProjectMutationIdentifier={{
                        ...exportProjectMutation.variables,
                        exportProjectId: exportProjectMutation.data?.exportProjectId,
                    }}
                    onResetProjectExport={exportProjectMutation.reset}
                />
            </>
        </CustomWellClickable>
    );
};
