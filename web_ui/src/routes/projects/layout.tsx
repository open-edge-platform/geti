// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Suspense } from 'react';

import { Grid, View } from '@adobe/react-spectrum';
import { Outlet } from 'react-router-dom';

import { isAnomalyDomain } from '../../core/projects/domains';
import { ProjectSidebar } from '../../pages/project-details/components/project-sidebar/project-sidebar.component';
import { useProject } from '../../pages/project-details/providers/project-provider/project-provider.component';
import { LandingPageHeader as Header } from '../../shared/components/header/header.component';
import { Loading } from '../../shared/components/loading/loading.component';

import classes from './../routes.module.scss';

export const ProjectLayout = (): JSX.Element => {
    const { project, isSingleDomainProject } = useProject();
    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);

    return (
        <Grid
            height={'100vh'}
            maxHeight={'100vh'}
            areas={['header header', 'sidebar content']}
            columns={{ L: ['size-3400', 'auto'], base: ['size-600', 'auto'] }}
            rows={['size-600', 'auto']}
        >
            <View gridArea={'header'}>
                <Header withBackButton isProject isAnomalyProject={isAnomalyProject} />
            </View>
            <View backgroundColor='gray-75' gridArea={'sidebar'} position='relative'>
                <ProjectSidebar project={project} />
            </View>
            <View
                UNSAFE_className={classes.innerContent}
                maxHeight={'100%'}
                height={'100%'}
                position={'relative'}
                gridArea={'content'}
                overflow={'hidden'}
                backgroundColor={'gray-50'}
                left={'50%'}
                paddingX={{ L: 'size-800', base: 'size-400' }}
                paddingY={{ L: 'size-450', base: 'size-300' }}
            >
                <Suspense fallback={<Loading size='L' />}>
                    <Outlet />
                </Suspense>
            </View>
        </Grid>
    );
};
