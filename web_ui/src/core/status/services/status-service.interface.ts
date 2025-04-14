// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { StatusProps } from '../status.interface';

export interface StatusService {
    getStatus(organizationId?: string): Promise<StatusProps>;
}
