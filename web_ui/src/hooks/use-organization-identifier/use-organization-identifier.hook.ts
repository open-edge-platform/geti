// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useParams } from 'react-router-dom';

import { OrganizationIdentifier } from '../../core/organizations/organizations.interface';

export const useOrganizationIdentifier = (): OrganizationIdentifier => {
    return useParams<Partial<OrganizationIdentifier>>() as OrganizationIdentifier;
};
