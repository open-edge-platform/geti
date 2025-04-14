// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@adobe/react-spectrum';

import { Datasets, Deployments, Model, Shield, Tag, Users } from '../../../../assets/icons';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ProjectProps } from '../../../../core/projects/project.interface';
import { isKeypointTask } from '../../../../core/projects/utils';
import { paths } from '../../../../core/services/routes';
import { RESOURCE_TYPE } from '../../../../core/users/users.interface';
import { Arrow } from '../../../../shared/components/arrow/arrow.component';
import { DomainName } from '../../../../shared/components/domain-name/domain-name.component';
import { useCheckPermission } from '../../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../../shared/components/has-permission/has-permission.interface';
import { MenuItemImage } from '../../../../shared/components/menu-item-image/menu-item-image.component';
import { MenuOption, MenuOptionTextAndIcon } from '../../../../shared/components/menu-option.interface';
import { ProjectNameDomain } from '../../../../shared/components/project-name-domain/project-name-domain.component';
import { SidebarMenu } from '../../../../shared/components/sidebar-menu/sidebar-menu.component';
import { isNotCropDomain } from '../../../../shared/utils';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';
import { ProjectThumbnail } from '../../../landing-page/landing-page-workspace/components/projects-list/components/project/project-thumbnail.component';
import { Performance } from './performance.component';

import classes from './project-sidebar.module.scss';

interface ProjectSidebarProps {
    project: ProjectProps;
}

export const ProjectSidebar = ({ project }: ProjectSidebarProps): JSX.Element => {
    const datasetIdentifier = useDatasetIdentifier();
    const canEditProjectName = useCheckPermission(
        [OPERATION.PROJECT_NAME_EDITION],
        [
            {
                type: RESOURCE_TYPE.PROJECT,
                id: project.id,
            },
        ]
    );

    const { organizationId, workspaceId } = datasetIdentifier;

    const { name, thumbnail, domains, tasks } = project;
    const filteredDomains = domains.filter(isNotCropDomain);

    const iconOptions: MenuOptionTextAndIcon[] = [
        {
            id: 'datasets',
            name: 'Datasets',
            ariaLabel: 'datasets',
            icon: (
                <MenuItemImage>
                    <Datasets width={'100%'} height={'100%'} />
                </MenuItemImage>
            ),
            url: paths.project.dataset.media(datasetIdentifier),
        },
        {
            id: 'models',
            name: 'Models',
            ariaLabel: 'models',
            icon: (
                <MenuItemImage>
                    <Model width={'100%'} height={'100%'} />
                </MenuItemImage>
            ),
            url: paths.project.models.index({ organizationId, workspaceId, projectId: project.id }),
        },
        {
            id: 'tests',
            name: 'Tests',
            ariaLabel: 'tests',
            icon: (
                <MenuItemImage>
                    <Shield width={'100%'} height={'100%'} />
                </MenuItemImage>
            ),
            url: paths.project.tests.index({ organizationId, workspaceId, projectId: project.id }),
        },
        {
            id: 'deployments',
            name: 'Deployments',
            ariaLabel: 'deployments',
            icon: (
                <MenuItemImage>
                    <Deployments width={'100%'} height={'100%'} />
                </MenuItemImage>
            ),
            url: paths.project.deployments({ organizationId, workspaceId, projectId: project.id }),
        },
    ];

    const isKeypoint = tasks.some(isKeypointTask);

    const options: MenuOption[][] = [
        [...iconOptions],
        [
            {
                id: isKeypoint ? 'template' : 'labels',
                name: isKeypoint ? 'Template' : 'Labels',
                ariaLabel: isKeypoint ? 'template' : 'labels',
                icon: (
                    <MenuItemImage>
                        <Tag width={'100%'} height={'100%'} />
                    </MenuItemImage>
                ),
                url: isKeypoint
                    ? paths.project.template({ organizationId, workspaceId, projectId: project.id })
                    : paths.project.labels({ organizationId, workspaceId, projectId: project.id }),
            },
            {
                id: 'users',
                name: 'Users',
                ariaLabel: 'Users',
                icon: (
                    <MenuItemImage>
                        <Users width={'100%'} height={'100%'} />
                    </MenuItemImage>
                ),
                url: paths.project.users({ organizationId, workspaceId, projectId: project.id }),
            },
        ],
    ];

    return (
        <Flex height={'100%'} direction={'column'} UNSAFE_className={classes.projectSidebar}>
            <Flex direction='column' gap={'size-200'} UNSAFE_className={classes.thumbnailContainer}>
                <ProjectNameDomain
                    classname={classes.projectNameContainer}
                    project={project}
                    isEditableName={canEditProjectName}
                />
                <Flex direction={'row'} gap={'size-100'}>
                    <ProjectThumbnail
                        alt={name}
                        width={48}
                        height={48}
                        thumbnail={thumbnail}
                        className={classes.thumbnail}
                        errorClassName={classes.thumbnailPlaceholder}
                        id={`project-page-sidebar-image-${idMatchingFormat(name)}`}
                    />
                    <Flex direction={'column'} UNSAFE_className={classes.thumbnailPlaceholder}>
                        <div aria-label='Project type'>
                            <Flex>
                                {filteredDomains.map((domain: DOMAIN, index: number) => {
                                    const shouldShowArrow = index < filteredDomains.length - 1;

                                    return (
                                        <Text key={domain} marginEnd={'size-25'}>
                                            <DomainName domain={domain} />
                                            <Arrow isHidden={!shouldShowArrow} />
                                        </Text>
                                    );
                                })}
                            </Flex>
                        </div>
                        <Performance project={project} />
                    </Flex>
                </Flex>
            </Flex>
            <Flex direction={'column'} justifyContent={'space-between'} height={'100%'} marginBottom={'size-300'}>
                <SidebarMenu options={options} id={'project-steps'} />
            </Flex>
        </Flex>
    );
};
