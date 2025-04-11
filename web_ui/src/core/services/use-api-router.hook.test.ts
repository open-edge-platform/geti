// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { renderHook } from '@testing-library/react';

import { MEDIA_TYPE } from '../media/base-media.interface';
import { useApiRouter } from './use-api-router.hook';
import { useDeploymentConfigQuery } from './use-deployment-config-query.hook';

jest.mock('./use-deployment-config-query.hook', () => ({
    useDeploymentConfigQuery: jest.fn(),
}));

const mockDeploymentConfig = (url: null | string) => {
    const data = {
        servingMode: 'on-prem',
        auth: {
            type: 'dex',
            authority: '/dex',
            clientId: 'web_ui',
        },
        dataPlaneUrl: url,
        controlPlaneUrl: url,
    } as const;

    // @ts-expect-error We only use data
    jest.mocked(useDeploymentConfigQuery).mockReturnValue({ data });
};

describe('useApiRouter', () => {
    const projectIdentifier = {
        organizationId: 'organization-id',
        projectId: 'project-id',
        workspaceId: 'workspace-id',
    };
    it('wihout a provided data or control plane returns a api route without base url', async () => {
        mockDeploymentConfig(null);

        const { result } = renderHook(() => useApiRouter());
        expect(result.current).not.toBeUndefined();

        expect(result.current.ACTIVATE_MODEL({ ...projectIdentifier, groupId: 'group' })).toEqual(
            '/api/v1/organizations/organization-id/workspaces/workspace-id/projects/project-id/model_groups/group:activate'
        );
        expect(result.current.ORGANIZATIONS).toEqual('/api/v1/organizations');
        expect(result.current.DATASET.IMPORT_TUS(projectIdentifier)).toEqual(
            '/api/v1/organizations/organization-id/workspaces/workspace-id/datasets/uploads/resumable'
        );
        expect(result.current.ANALYTICS.DASHBOARD).toEqual('/api/v1/grafana');

        expect(
            result.current.MEDIA_ITEM_SRC(
                { ...projectIdentifier, datasetId: 'dataset-id' },
                { type: MEDIA_TYPE.IMAGE, imageId: 'image-id' }
            )
        ).toEqual(
            '/api/v1/organizations/organization-id/workspaces/workspace-id/projects/project-id/datasets/dataset-id/media/images/image-id/display/full'
        );

        expect(result.current.PREFIX('api/v1/route')).toEqual('/api/v1/route');
    });

    it('with a provided data or control plane returns a api route without base url', async () => {
        mockDeploymentConfig('https://app.geti.intel.com');

        const { result } = renderHook(() => useApiRouter());
        expect(result.current).not.toBeUndefined();

        expect(result.current.ACTIVATE_MODEL({ ...projectIdentifier, groupId: 'group' })).toEqual(
            'https://app.geti.intel.com/api/v1/organizations/organization-id/workspaces/workspace-id/projects/project-id/model_groups/group:activate'
        );
        expect(result.current.ORGANIZATIONS).toEqual('https://app.geti.intel.com/api/v1/organizations');
        expect(result.current.DATASET.IMPORT_TUS(projectIdentifier)).toEqual(
            'https://app.geti.intel.com/api/v1/organizations/organization-id/workspaces/workspace-id/datasets/uploads/resumable'
        );
        expect(result.current.ANALYTICS.DASHBOARD).toEqual('https://app.geti.intel.com/api/v1/grafana');
        expect(
            result.current.MEDIA_ITEM_SRC(
                { ...projectIdentifier, datasetId: 'dataset-id' },
                { type: MEDIA_TYPE.IMAGE, imageId: 'image-id' }
            )
        ).toEqual(
            'https://app.geti.intel.com/api/v1/organizations/organization-id/workspaces/workspace-id/projects/project-id/datasets/dataset-id/media/images/image-id/display/full'
        );

        expect(result.current.PREFIX('api/v1/route')).toEqual('https://app.geti.intel.com/api/v1/route');
    });

    it('does not crash when provided with undefined behaviour', async () => {
        mockDeploymentConfig('https://app.geti.intel.com');

        const { result } = renderHook(() => useApiRouter());
        expect(result.current).not.toBeUndefined();

        // @ts-expect-error The routing interface doens't allow undefined values,
        // however it is possible that an undefined value is passed when we don't perform
        // validation on an api request's response
        expect(result.current.PREFIX(undefined as string)).toEqual('https://app.geti.intel.com');
    });

    it('does not prefix a url', async () => {
        mockDeploymentConfig('https://app.geti.intel.com');

        const { result } = renderHook(() => useApiRouter());
        expect(result.current).not.toBeUndefined();

        expect(result.current.PREFIX('https://app.geti.intel.com')).not.toEqual(
            'https://app.geti.intel.com/api/https://app.geti.intel.com'
        );
        expect(result.current.PREFIX('https://app.geti.intel.com')).toEqual('https://app.geti.intel.com');
    });
});
