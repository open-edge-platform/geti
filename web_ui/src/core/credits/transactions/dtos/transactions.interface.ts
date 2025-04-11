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

import { ResponseTotalsDTO } from '../../dtos/credits.interface';
import { CreditServiceName, TransactionsAggregatesKey } from '../transactions.interface';

export interface TransactionsResponseDTO extends ResponseTotalsDTO {
    transactions: {
        credits: number;
        workspace_id: string;
        project_id: string;
        service_name: CreditServiceName;
        milliseconds_timestamp: number;
    }[];
}

export interface TransactionsAggregatesDTO extends ResponseTotalsDTO {
    aggregates: {
        group: {
            key: TransactionsAggregatesKey;
            value: string;
        }[];
        result: {
            credits: number;
            resources: {
                [key: string]: number | undefined;
            };
        };
    }[];
}
