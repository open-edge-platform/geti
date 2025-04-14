// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
