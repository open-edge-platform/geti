// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Loading } from '@shared/components/loading/loading.component';
import { PageLayout } from '@shared/components/page-layout/page-layout.component';
import { useParams } from 'react-router-dom';

import { paths } from '../../../../core/services/routes';
import { useTests } from '../../../../core/tests/hooks/use-tests.hook';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { TestDetails } from './test-details.component';

export const ProjectTest = (): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();
    const { testId } = useParams<{ testId: string }>();

    const { useTestQuery } = useTests();
    const { data: test, isLoading } = useTestQuery(projectIdentifier, testId ?? '');

    return (
        <PageLayout
            breadcrumbs={[
                { id: 'tests-id', breadcrumb: 'Tests', href: paths.project.tests.index(projectIdentifier) },
                { id: 'test-id', breadcrumb: test?.testName },
            ]}
        >
            {isLoading || !test ? <Loading /> : <TestDetails test={test} />}
        </PageLayout>
    );
};
