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

import { UseMutationResult, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { OverlayTriggerState } from 'react-stately';

export interface PartialPersonalAccessToken {
    id: string;
    partial: string;
    name: string;
    description: string;
    expiresAt: string;
    organizationId: string;
    userId: string;
    createdAt: string;
}

export interface PersonalAccessToken extends PartialPersonalAccessToken {
    personalAccessToken: string;
}

export interface PersonalAccessTokens {
    personalAccessTokens: PartialPersonalAccessToken[];
}

export interface BaseTokenProps {
    organizationId: string;
    userId: string;
}

export interface CreatePersonalAccessTokenDialogProps extends BaseTokenProps {
    triggerState: OverlayTriggerState;
}

export interface CreatePersonalAccessTokenPayload extends BaseTokenProps {
    name: string;
    description: string;
    expirationDate: string;
}

export interface DeletePersonalAccessTokenPayload extends BaseTokenProps {
    tokenId: string;
}

export interface UpdatePersonalAccessTokenPayload extends DeletePersonalAccessTokenPayload {
    expirationDate: string;
}

export interface PersonalAccessTokensService {
    deletePersonalAccessToken: (props: DeletePersonalAccessTokenPayload) => Promise<void>;
    getPersonalAccessTokens: (props: BaseTokenProps) => Promise<PersonalAccessTokens>;
    createPersonalAccessToken: (props: CreatePersonalAccessTokenPayload) => Promise<PersonalAccessToken>;
    updatePersonalAccessToken: (props: UpdatePersonalAccessTokenPayload) => Promise<PartialPersonalAccessToken>;
}

export interface UsePersonalAccessToken {
    useGetPersonalAccessTokensQuery: (props: BaseTokenProps) => UseQueryResult<PersonalAccessTokens, AxiosError>;
    deletePersonalAccessTokenMutation: UseMutationResult<void, AxiosError, DeletePersonalAccessTokenPayload>;
    createPersonalAccessTokenMutation: UseMutationResult<
        PersonalAccessToken,
        AxiosError,
        CreatePersonalAccessTokenPayload
    >;
    updatePersonalAccessTokenMutation: UseMutationResult<
        PartialPersonalAccessToken,
        AxiosError,
        UpdatePersonalAccessTokenPayload
    >;
}
