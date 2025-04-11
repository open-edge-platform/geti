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

import {
    CreatePersonalAccessTokenPayload,
    PartialPersonalAccessToken,
    PersonalAccessToken,
    PersonalAccessTokens,
    PersonalAccessTokensService,
} from './personal-access-tokens.interface';

export const createInMemoryPersonalAccessTokensService = (): PersonalAccessTokensService => {
    const createPersonalAccessToken = async (
        _props: CreatePersonalAccessTokenPayload
    ): Promise<PersonalAccessToken> => {
        return Promise.resolve({
            id: '4a5f12e2-2bbb-435a-910b-28949f739650',
            partial: 'geti_pat_dNSBPdJ1Y9S',
            name: 'name',
            description: 'description',
            expiresAt: '2024-06-20T11:11:11.062Z',
            organizationId: 'de61b273-a8cf-4dd7-96a4-b5e1c5b131fd',
            userId: 'b82da6f8-5352-4dbb-99d7-84135a811bea',
            createdAt: '2024-02-08T12:17:26Z',
            personalAccessToken: 'JRR Token',
        });
    };

    const getPersonalAccessTokens = async (): Promise<PersonalAccessTokens> => {
        return Promise.resolve({
            personalAccessTokens: [
                {
                    id: '4a5f12e2-2bbb-435a-910b-28949f739650',
                    partial: 'geti_pat_dNSBPdJ1Y9S',
                    name: 'name',
                    description: 'description',
                    expiresAt: '2024-06-20T11:11:11.062Z',
                    organizationId: 'de61b273-a8cf-4dd7-96a4-b5e1c5b131fd',
                    userId: 'b82da6f8-5352-4dbb-99d7-84135a811bea',
                    createdAt: '2024-02-08T12:17:26Z',
                },
            ],
        });
    };

    const deletePersonalAccessToken = async (): Promise<void> => {
        return Promise.resolve();
    };

    const updatePersonalAccessToken = async (): Promise<PartialPersonalAccessToken> => {
        return Promise.resolve({
            id: '4a5f12e2-2bbb-435a-910b-28949f739650',
            partial: 'geti_pat_dNSBPdJ1Y9S',
            name: 'name',
            description: 'description',
            expiresAt: '2024-06-20T11:11:11.062Z',
            organizationId: 'de61b273-a8cf-4dd7-96a4-b5e1c5b131fd',
            userId: 'b82da6f8-5352-4dbb-99d7-84135a811bea',
            createdAt: '2024-02-08T12:17:26Z',
        });
    };

    return { createPersonalAccessToken, getPersonalAccessTokens, deletePersonalAccessToken, updatePersonalAccessToken };
};
