// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useParams } from 'react-router-dom';

import { paths } from '../../../../core/services/routes';
import { useTests } from '../../../../core/tests/hooks/use-tests.hook';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { Loading } from '../../../../shared/components/loading/loading.component';
import { PageLayout } from '../../../../shared/components/page-layout/page-layout.component';
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
