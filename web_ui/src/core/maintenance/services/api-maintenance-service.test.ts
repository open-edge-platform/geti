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

import { rest } from 'msw';

import { server } from '../../annotations/services/test-utils';
import { createApiMaintenanceService } from './api-maintenance-service';

const mockStartTimeTimestamp = 1711312113376; //  Mar 24 2024 21:28h
const mockEndTimeTimestamp = 1711513116880; //  Mar 27 2024 05:18h
const mockMaintenanceConfigUrl = 'some-config-url';

describe('MaintenanceService', () => {
    const maintenanceService = createApiMaintenanceService();

    it('success case', async () => {
        server.use(
            rest.get(mockMaintenanceConfigUrl, (_req, res, ctx) => {
                return res(
                    ctx.status(200),
                    ctx.json({
                        maintenance: {
                            enabled: true,
                            window: {
                                start: mockStartTimeTimestamp,
                                end: mockEndTimeTimestamp,
                            },
                        },
                    })
                );
            })
        );
        const response = await maintenanceService.getMaintenanceInfo(mockMaintenanceConfigUrl);

        expect(response).toEqual({
            maintenance: {
                enabled: true,
                window: {
                    start: mockStartTimeTimestamp,
                    end: mockEndTimeTimestamp,
                },
            },
        });
    });

    it('error case', async () => {
        server.use(
            rest.get(mockMaintenanceConfigUrl, (_req, res, ctx) => {
                return res(ctx.status(404));
            })
        );

        const response = maintenanceService.getMaintenanceInfo(mockMaintenanceConfigUrl);

        return expect(response).rejects.toThrowError('The server can not find requested resource');
    });
});
