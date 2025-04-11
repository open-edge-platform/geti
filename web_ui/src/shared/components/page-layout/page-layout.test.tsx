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

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { getById } from '../../../test-utils/utils';
import { PageLayout } from './page-layout.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: '123',
        organizationId: 'organization-123',
    }),
    useLocation: () => ({
        pathname:
            'localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/123/media',
    }),
}));

describe('Project page content', () => {
    it('Check if all elements are on the screen', async () => {
        const { container } = render(
            <PageLayout breadcrumbs={[{ id: 'this-is-test-title-id', breadcrumb: 'This is test title' }]}>
                <></>
            </PageLayout>
        );

        expect(getById(container, 'page-layout-id')).toBeInTheDocument();
        const title = getById(container, 'this-is-test-title-id');
        expect(title?.textContent).toBe('This is test title');
    });
});
