// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
